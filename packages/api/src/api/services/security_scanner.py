"""CodeWarden Security Scanner Service.

Server-side security scanning that integrates with the SDK scanners.
Supports:
- Dependency scanning (pip-audit)
- Secret scanning (Gitleaks patterns)
- Code scanning (Bandit SAST)

The service can scan:
1. Server's own codebase (for testing)
2. Uploaded code archives
3. Git repositories (via clone)
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScanFinding:
    """A security finding from any scanner."""

    type: str  # 'dependency', 'secret', 'code'
    severity: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    cwe_id: str | None = None
    cve_id: str | None = None
    package_name: str | None = None
    package_version: str | None = None
    fixed_version: str | None = None
    remediation: str | None = None
    raw_data: dict | None = None


@dataclass
class ScanResult:
    """Combined result from all scanners."""

    findings: list[ScanFinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    severity_counts: dict[str, int] = field(
        default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0}
    )
    fix_commands: list[str] = field(default_factory=list)


class SecurityScanner:
    """Server-side security scanner.

    Uses the same patterns and logic as the SDK scanners but runs
    on the server to scan code repositories or uploaded archives.
    """

    # Gitleaks-derived patterns for secret detection
    SECRET_PATTERNS: dict[str, dict[str, Any]] = {
        "aws_access_key": {
            "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "severity": "critical",
            "description": "AWS Access Key ID detected",
        },
        "aws_secret_key": {
            "pattern": r"(?i)aws[_\-\.]?(?:secret[_\-\.]?)?(?:access[_\-\.]?)?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            "severity": "critical",
            "description": "AWS Secret Access Key detected",
        },
        "github_token": {
            "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
            "severity": "critical",
            "description": "GitHub Personal Access Token detected",
        },
        "stripe_live_key": {
            "pattern": r"sk_live_[0-9a-zA-Z]{24,}",
            "severity": "critical",
            "description": "Stripe Live Secret Key detected",
        },
        "stripe_test_key": {
            "pattern": r"sk_test_[0-9a-zA-Z]{24,}",
            "severity": "medium",
            "description": "Stripe Test Secret Key detected",
        },
        "openai_api_key": {
            "pattern": r"sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}",
            "severity": "critical",
            "description": "OpenAI API Key detected",
        },
        "anthropic_api_key": {
            "pattern": r"sk-ant-[A-Za-z0-9_-]{80,}",
            "severity": "critical",
            "description": "Anthropic API Key detected",
        },
        "google_api_key": {
            "pattern": r"AIza[0-9A-Za-z\-_]{35}",
            "severity": "high",
            "description": "Google API Key detected",
        },
        "slack_token": {
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
            "severity": "high",
            "description": "Slack Token detected",
        },
        "private_key": {
            "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "severity": "critical",
            "description": "Private Key detected",
        },
        "jwt_token": {
            "pattern": r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
            "severity": "high",
            "description": "JWT Token detected",
        },
        "database_url": {
            "pattern": r"(?:postgres|mysql|mongodb|redis)://[^:]+:[^@]+@[^\s]+",
            "severity": "critical",
            "description": "Database connection string with credentials detected",
        },
        "password_assignment": {
            "pattern": r'(?i)(?:password|passwd|pwd|secret|api[_-]?key|auth[_-]?token)[\'"]?\s*[:=]\s*[\'"][^\'"]{8,}[\'"]',
            "severity": "high",
            "description": "Hardcoded password or secret detected",
        },
    }

    # CWE mappings for Bandit test IDs
    CWE_MAPPINGS: dict[str, str] = {
        "B101": "CWE-703",
        "B102": "CWE-78",
        "B103": "CWE-732",
        "B104": "CWE-200",
        "B105": "CWE-259",
        "B106": "CWE-259",
        "B107": "CWE-259",
        "B301": "CWE-502",
        "B303": "CWE-327",
        "B307": "CWE-78",
        "B311": "CWE-330",
        "B501": "CWE-295",
        "B506": "CWE-89",
        "B602": "CWE-78",
        "B608": "CWE-89",
    }

    def __init__(self, target_path: str | None = None):
        """Initialize scanner.

        Args:
            target_path: Path to scan. If None, scans current directory.
        """
        self.target_path = Path(target_path) if target_path else Path.cwd()
        self._compiled_patterns: dict = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile secret detection patterns."""
        import re

        for name, config in self.SECRET_PATTERNS.items():
            try:
                self._compiled_patterns[name] = (
                    re.compile(config["pattern"]),
                    config,
                )
            except re.error as e:
                logger.warning(f"Invalid secret pattern '{name}': {e}")

    def scan(
        self,
        scan_dependencies: bool = True,
        scan_secrets: bool = True,
        scan_code: bool = True,
    ) -> ScanResult:
        """Run security scan.

        Args:
            scan_dependencies: Run dependency vulnerability scan
            scan_secrets: Run secret detection scan
            scan_code: Run static code analysis

        Returns:
            ScanResult with all findings
        """
        result = ScanResult()

        if scan_dependencies:
            dep_result = self._scan_dependencies()
            result.findings.extend(dep_result.findings)
            result.errors.extend(dep_result.errors)
            result.fix_commands.extend(dep_result.fix_commands)

        if scan_secrets:
            secret_result = self._scan_secrets()
            result.findings.extend(secret_result.findings)
            result.errors.extend(secret_result.errors)

        if scan_code:
            code_result = self._scan_code()
            result.findings.extend(code_result.findings)
            result.errors.extend(code_result.errors)

        # Calculate severity counts
        for finding in result.findings:
            if finding.severity in result.severity_counts:
                result.severity_counts[finding.severity] += 1

        return result

    def _scan_dependencies(self) -> ScanResult:
        """Scan dependencies using pip-audit."""
        import json

        result = ScanResult()

        if not shutil.which("pip-audit"):
            result.errors.append(
                "pip-audit not installed. Install with: pip install pip-audit"
            )
            return result

        try:
            # Check for requirements.txt in target path
            req_file = self.target_path / "requirements.txt"

            cmd = ["pip-audit", "--format", "json", "--progress-spinner", "off"]
            if req_file.exists():
                cmd.extend(["--requirement", str(req_file)])
            else:
                cmd.append("--skip-editable")

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.target_path),
            )

            # pip-audit returns exit code 1 when vulnerabilities found
            if proc.returncode not in (0, 1):
                if proc.stderr:
                    result.errors.append(f"pip-audit error: {proc.stderr}")
                return result

            if not proc.stdout.strip():
                return result

            data = json.loads(proc.stdout)
            dependencies = (
                data if isinstance(data, list) else data.get("dependencies", [])
            )

            for dep in dependencies:
                package_name = dep.get("name", "unknown")
                package_version = dep.get("version", "unknown")

                for vuln in dep.get("vulns", []):
                    vuln_id = vuln.get("id", "UNKNOWN")
                    description = vuln.get("description", "No description available")
                    fix_versions = vuln.get("fix_versions", [])
                    aliases = vuln.get("aliases", [])

                    # Get CVE ID
                    cve_id = next(
                        (a for a in aliases if a.startswith("CVE-")), vuln_id
                    )

                    # Determine severity from CVSS score
                    severity = self._get_severity_from_cvss(vuln)

                    # Build remediation
                    fixed = fix_versions[0] if fix_versions else None
                    remediation = (
                        f"Upgrade {package_name} to version {fixed} or later"
                        if fixed
                        else f"Check {cve_id} for fix information"
                    )

                    result.findings.append(
                        ScanFinding(
                            type="dependency",
                            severity=severity,
                            title=f"Vulnerable dependency: {package_name} ({vuln_id})",
                            description=description,
                            package_name=package_name,
                            package_version=package_version,
                            fixed_version=fixed,
                            cve_id=cve_id,
                            remediation=remediation,
                            raw_data=vuln,
                        )
                    )

                    if fixed:
                        result.fix_commands.append(
                            f"pip install --upgrade {package_name}>={fixed}"
                        )

        except subprocess.TimeoutExpired:
            result.errors.append("pip-audit timed out after 120 seconds")
        except json.JSONDecodeError as e:
            result.errors.append(f"Failed to parse pip-audit output: {e}")
        except Exception as e:
            result.errors.append(f"Dependency scan error: {e}")

        return result

    def _get_severity_from_cvss(self, vuln: dict) -> str:
        """Determine severity from CVSS score."""
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

        # Check severity field
        severity = vuln.get("severity", "").lower()
        if severity in ("critical", "high", "medium", "low"):
            return severity

        return "high"  # Default for known vulnerabilities

    def _scan_secrets(self) -> ScanResult:
        """Scan for hardcoded secrets."""
        result = ScanResult()

        # File extensions to scan
        scan_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".json",
            ".yml",
            ".yaml",
            ".env",
            ".cfg",
            ".ini",
            ".toml",
            ".sh",
            ".bash",
        }

        # Directories to skip
        skip_dirs = {
            ".git",
            "node_modules",
            "__pycache__",
            "venv",
            ".venv",
            "dist",
            "build",
            ".pytest_cache",
        }

        if not self.target_path.exists():
            result.errors.append(f"Target path does not exist: {self.target_path}")
            return result

        try:
            for root, dirs, files in os.walk(self.target_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in skip_dirs]

                for file in files:
                    file_path = Path(root) / file

                    # Check extension
                    if file_path.suffix.lower() not in scan_extensions:
                        if file_path.name not in {".env", ".envrc", "Dockerfile"}:
                            continue

                    # Skip large files (>1MB)
                    try:
                        if file_path.stat().st_size > 1024 * 1024:
                            continue
                    except OSError:
                        continue

                    self._scan_file_for_secrets(file_path, result)

        except Exception as e:
            result.errors.append(f"Secret scan error: {e}")

        return result

    def _scan_file_for_secrets(self, file_path: Path, result: ScanResult) -> None:
        """Scan a single file for secrets."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            result.errors.append(f"Could not read {file_path}: {e}")
            return

        lines = content.split("\n")
        try:
            relative_path = str(file_path.relative_to(self.target_path))
        except ValueError:
            relative_path = str(file_path)

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            for pattern_name, (compiled, config) in self._compiled_patterns.items():
                matches = compiled.finditer(line)
                for match in matches:
                    # Skip false positives
                    if self._is_false_positive(line, match.group(), file_path):
                        continue

                    result.findings.append(
                        ScanFinding(
                            type="secret",
                            severity=config.get("severity", "high"),
                            title=config.get(
                                "description", f"Secret detected: {pattern_name}"
                            ),
                            description=f"Potential {pattern_name.replace('_', ' ')} found in source code",
                            file_path=relative_path,
                            line_number=line_num,
                            column_number=match.start() + 1,
                            remediation="Remove the hardcoded secret and use environment variables or a secrets manager instead",
                            raw_data={
                                "pattern_name": pattern_name,
                                "matched_text": self._redact_secret(match.group()),
                            },
                        )
                    )

    def _is_false_positive(self, line: str, match: str, file_path: Path) -> bool:
        """Check if a match is likely a false positive."""
        line_lower = line.lower()

        # Common false positive indicators
        false_positive_indicators = [
            "example",
            "sample",
            "placeholder",
            "your_",
            "xxx",
            "fake",
            "test",
            "dummy",
            "<your",
            "${",
            "{{",
            "process.env",
            "os.environ",
            "os.getenv",
        ]

        for indicator in false_positive_indicators:
            if indicator in line_lower:
                return True

        # Skip documentation
        if file_path.suffix.lower() in {".md", ".rst", ".txt"}:
            return True

        # Skip if match is all same character (placeholder)
        if len(set(match.replace("-", "").replace("_", ""))) <= 2:
            return True

        return False

    def _redact_secret(self, secret: str, visible_chars: int = 4) -> str:
        """Redact a secret, showing only first/last few characters."""
        if len(secret) <= visible_chars * 2:
            return "*" * len(secret)
        return (
            secret[:visible_chars]
            + "*" * (len(secret) - visible_chars * 2)
            + secret[-visible_chars:]
        )

    def _scan_code(self) -> ScanResult:
        """Scan code using Bandit for security issues."""
        import json

        result = ScanResult()

        if not shutil.which("bandit"):
            result.errors.append(
                "Bandit not installed. Install with: pip install bandit"
            )
            return result

        if not self.target_path.exists():
            result.errors.append(f"Target path does not exist: {self.target_path}")
            return result

        try:
            cmd = [
                "bandit",
                "-r",  # Recursive
                "-f",
                "json",  # JSON output
                "-ll",  # Medium severity and above
                "--exclude",
                "venv,.venv,node_modules,.git",
                str(self.target_path),
            ]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Bandit returns non-zero when issues found
            output = proc.stdout
            if not output and proc.returncode not in (0, 1):
                if proc.stderr:
                    result.errors.append(f"Bandit error: {proc.stderr}")
                return result

            if not output.strip():
                return result

            data = json.loads(output)

            for issue in data.get("results", []):
                test_id = issue.get("test_id", "")
                severity = self._map_bandit_severity(
                    issue.get("issue_severity", "MEDIUM"),
                    issue.get("issue_confidence", "MEDIUM"),
                )

                # Get relative file path
                file_path = issue.get("filename", "")
                try:
                    file_path = str(Path(file_path).relative_to(self.target_path))
                except ValueError:
                    pass

                result.findings.append(
                    ScanFinding(
                        type="code",
                        severity=severity,
                        title=f"{test_id}: {issue.get('test_name', 'Security Issue')}",
                        description=issue.get("issue_text", "Security issue detected"),
                        file_path=file_path,
                        line_number=issue.get("line_number"),
                        column_number=issue.get("col_offset"),
                        cwe_id=self.CWE_MAPPINGS.get(test_id),
                        remediation=self._get_bandit_remediation(
                            test_id, issue.get("test_name", "")
                        ),
                        raw_data={
                            "test_id": test_id,
                            "test_name": issue.get("test_name"),
                            "issue_severity": issue.get("issue_severity"),
                            "issue_confidence": issue.get("issue_confidence"),
                            "code": issue.get("code", ""),
                            "more_info": issue.get("more_info", ""),
                        },
                    )
                )

        except subprocess.TimeoutExpired:
            result.errors.append("Bandit scan timed out after 300 seconds")
        except json.JSONDecodeError as e:
            result.errors.append(f"Failed to parse Bandit output: {e}")
        except Exception as e:
            result.errors.append(f"Code scan error: {e}")

        return result

    def _map_bandit_severity(
        self, bandit_severity: str, bandit_confidence: str
    ) -> str:
        """Map Bandit severity and confidence to our severity levels."""
        severity_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
        base_severity = severity_map.get(bandit_severity.upper(), "medium")

        # Boost to critical for high confidence + high severity
        if bandit_confidence.upper() == "HIGH" and base_severity == "high":
            return "critical"

        return base_severity

    def _get_bandit_remediation(self, test_id: str, test_name: str) -> str:
        """Get remediation advice for Bandit findings."""
        remediations = {
            "B101": "Remove assert statements from production code. Use proper exception handling instead.",
            "B102": "Avoid using exec(). Use safer alternatives like importlib for dynamic imports.",
            "B103": "Use more restrictive file permissions (e.g., 0o600 for sensitive files).",
            "B104": "Bind to specific IP addresses instead of 0.0.0.0 in production.",
            "B105": "Use environment variables or a secrets manager instead of hardcoded passwords.",
            "B106": "Use environment variables or a secrets manager instead of hardcoded passwords.",
            "B107": "Use environment variables or a secrets manager instead of hardcoded passwords.",
            "B108": "Use tempfile.mkstemp() or tempfile.TemporaryDirectory().",
            "B110": "Handle exceptions explicitly instead of using bare except with pass.",
            "B201": "Set debug=False in production Flask applications.",
            "B301": "Avoid pickle for untrusted data. Use JSON or other safe formats.",
            "B303": "Use SHA-256 or stronger hashing algorithms instead of MD5/SHA1.",
            "B306": "Use tempfile.mkstemp() instead of mktemp().",
            "B307": "Avoid eval(). Use ast.literal_eval() for safe evaluation.",
            "B310": "Validate and sanitize URLs before making requests.",
            "B311": "Use secrets module instead of random for security operations.",
            "B501": "Enable certificate verification in requests (verify=True).",
            "B502": "Use TLS 1.2 or higher. Avoid older SSL/TLS versions.",
            "B506": "Use yaml.safe_load() instead of yaml.load().",
            "B602": "Avoid shell=True in subprocess calls. Pass arguments as a list.",
            "B608": "Use parameterized queries instead of string formatting for SQL.",
        }

        return remediations.get(
            test_id,
            f"Review and fix the {test_name} security issue. "
            "Consult Bandit documentation for guidance.",
        )


def scan_codebase(
    target_path: str | None = None,
    scan_type: str = "full",
) -> ScanResult:
    """Convenience function to run a security scan.

    Args:
        target_path: Path to scan (defaults to current directory)
        scan_type: Type of scan - 'full', 'dependencies', 'secrets', 'code'

    Returns:
        ScanResult with all findings
    """
    scanner = SecurityScanner(target_path)

    return scanner.scan(
        scan_dependencies=scan_type in ("full", "dependencies"),
        scan_secrets=scan_type in ("full", "secrets"),
        scan_code=scan_type in ("full", "code"),
    )


def scan_git_repo(
    repo_url: str,
    branch: str = "main",
    scan_type: str = "full",
) -> ScanResult:
    """Clone and scan a git repository.

    Args:
        repo_url: Git repository URL
        branch: Branch to scan
        scan_type: Type of scan

    Returns:
        ScanResult with all findings
    """
    result = ScanResult()

    if not shutil.which("git"):
        result.errors.append("Git not installed")
        return result

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, repo_url, tmp_dir],
                capture_output=True,
                text=True,
                timeout=120,
                check=True,
            )

            # Run scan on cloned repo
            return scan_codebase(tmp_dir, scan_type)

        except subprocess.TimeoutExpired:
            result.errors.append("Git clone timed out")
        except subprocess.CalledProcessError as e:
            result.errors.append(f"Git clone failed: {e.stderr}")
        except Exception as e:
            result.errors.append(f"Repository scan error: {e}")

    return result
