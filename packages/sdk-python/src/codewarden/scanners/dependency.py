"""Dependency vulnerability scanner using pip-audit."""

import json
import shutil
import subprocess
import time
from typing import Optional

from codewarden.scanners.base import BaseScannerModule, ScanResult


class DependencyScanner(BaseScannerModule):
    """Scan Python dependencies for known vulnerabilities.

    Uses pip-audit to check installed packages against the
    Python Packaging Advisory Database (PyPI).

    Example:
        >>> scanner = DependencyScanner()
        >>> if scanner.is_available():
        ...     result = scanner.scan()
        ...     for finding in result.findings:
        ...         print(f"{finding.package_name}: {finding.cve_id}")
    """

    # Map pip-audit severity to our standard
    SEVERITY_MAP = {
        "critical": "critical",
        "high": "high",
        "moderate": "medium",
        "medium": "medium",
        "low": "low",
        "unknown": "medium",
    }

    def __init__(
        self,
        requirements_file: Optional[str] = None,
        skip_editable: bool = True,
        timeout: int = 120,
        config: Optional[dict] = None,
    ):
        """Initialize dependency scanner.

        Args:
            requirements_file: Path to requirements.txt (optional, scans environment if not provided)
            skip_editable: Skip editable installs
            timeout: Command timeout in seconds
            config: Additional configuration
        """
        super().__init__(config)
        self.requirements_file = requirements_file
        self.skip_editable = skip_editable
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if pip-audit is installed."""
        return shutil.which("pip-audit") is not None

    def scan(self) -> ScanResult:
        """Run pip-audit vulnerability scan.

        Returns:
            ScanResult with dependency vulnerabilities
        """
        start_time = time.time()
        self._findings = []
        self._errors = []

        if not self.is_available():
            self._errors.append(
                "pip-audit not found. Install with: pip install pip-audit"
            )
            return self._build_result(start_time)

        try:
            result = self._run_pip_audit()
            self._parse_results(result)
        except subprocess.TimeoutExpired:
            self._errors.append(f"pip-audit timed out after {self.timeout}s")
        except subprocess.CalledProcessError as e:
            # pip-audit returns non-zero if vulnerabilities found
            # so we need to parse stdout anyway
            if e.stdout:
                self._parse_results(e.stdout)
            else:
                self._errors.append(f"pip-audit failed: {e.stderr or str(e)}")
        except json.JSONDecodeError as e:
            self._errors.append(f"Failed to parse pip-audit output: {e}")
        except Exception as e:
            self._errors.append(f"Dependency scan error: {str(e)}")

        return self._build_result(start_time)

    def _run_pip_audit(self) -> str:
        """Execute pip-audit command.

        Returns:
            JSON output from pip-audit
        """
        cmd = ["pip-audit", "--format", "json", "--progress-spinner", "off"]

        if self.requirements_file:
            cmd.extend(["--requirement", self.requirements_file])

        if self.skip_editable:
            cmd.append("--skip-editable")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

        # pip-audit returns exit code 1 when vulnerabilities found
        # but still outputs valid JSON
        if result.returncode not in (0, 1):
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        return result.stdout

    def _parse_results(self, json_output: str) -> None:
        """Parse pip-audit JSON output into findings.

        Args:
            json_output: Raw JSON from pip-audit
        """
        if not json_output.strip():
            return

        data = json.loads(json_output)

        # Handle both old and new pip-audit output formats
        dependencies = data if isinstance(data, list) else data.get("dependencies", [])

        for dep in dependencies:
            package_name = dep.get("name", "unknown")
            package_version = dep.get("version", "unknown")
            vulns = dep.get("vulns", [])

            for vuln in vulns:
                vuln_id = vuln.get("id", "UNKNOWN")
                description = vuln.get("description", "No description available")
                fix_versions = vuln.get("fix_versions", [])
                aliases = vuln.get("aliases", [])

                # Determine severity
                severity = self._determine_severity(vuln)

                # Get CVE ID from aliases if available
                cve_id = None
                for alias in aliases:
                    if alias.startswith("CVE-"):
                        cve_id = alias
                        break

                # Build remediation message
                remediation = None
                if fix_versions:
                    fixed = fix_versions[0] if fix_versions else None
                    remediation = f"Upgrade {package_name} to version {fixed} or later"

                finding = self._create_finding(
                    type="dependency",
                    severity=severity,
                    title=f"Vulnerable dependency: {package_name} ({vuln_id})",
                    description=description,
                    package_name=package_name,
                    package_version=package_version,
                    fixed_version=fix_versions[0] if fix_versions else None,
                    cve_id=cve_id or vuln_id,
                    remediation=remediation,
                    raw_data=vuln,
                )
                self._findings.append(finding)

    def _determine_severity(self, vuln: dict) -> str:
        """Determine severity from vulnerability data.

        Args:
            vuln: Vulnerability dictionary

        Returns:
            Normalized severity string
        """
        # Try to get severity from various fields
        severity = vuln.get("severity")
        if severity:
            return self._normalize_severity(severity)

        # Check for CVSS score
        cvss = vuln.get("cvss_score") or vuln.get("cvss", {}).get("score")
        if cvss:
            try:
                score = float(cvss)
                if score >= 9.0:
                    return "critical"
                elif score >= 7.0:
                    return "high"
                elif score >= 4.0:
                    return "medium"
                else:
                    return "low"
            except (ValueError, TypeError):
                pass

        # Default to high for known vulnerabilities
        return "high"

    def _normalize_severity(self, severity: str) -> str:
        """Normalize pip-audit severity to standard values."""
        return self.SEVERITY_MAP.get(severity.lower(), "medium")
