"""CodeWarden Security Scanners.

This module provides security scanning capabilities for detecting:
- Vulnerable dependencies (pip-audit)
- Leaked secrets (Gitleaks patterns)
- Code security issues (Bandit SAST)
"""

from codewarden.scanners.base import BaseScannerModule, ScanFinding, ScanResult
from codewarden.scanners.dependency import DependencyScanner
from codewarden.scanners.secret import SecretScanner
from codewarden.scanners.code import CodeScanner

__all__ = [
    "BaseScannerModule",
    "ScanFinding",
    "ScanResult",
    "DependencyScanner",
    "SecretScanner",
    "CodeScanner",
    "run_security_scan",
    "SecurityAudit",
]


class SecurityAudit:
    """Orchestrate all security scanners."""

    def __init__(
        self,
        scan_dependencies: bool = True,
        scan_secrets: bool = True,
        scan_code: bool = True,
        target_path: str = ".",
    ):
        """Initialize security audit.

        Args:
            scan_dependencies: Run dependency vulnerability scan
            scan_secrets: Run secret detection scan
            scan_code: Run SAST code analysis
            target_path: Path to scan (default: current directory)
        """
        self.target_path = target_path
        self.scanners: list[BaseScannerModule] = []

        if scan_dependencies:
            self.scanners.append(DependencyScanner())
        if scan_secrets:
            self.scanners.append(SecretScanner(target_path=target_path))
        if scan_code:
            self.scanners.append(CodeScanner(target_path=target_path))

    def run(self) -> ScanResult:
        """Run all configured scanners.

        Returns:
            Combined scan result with all findings
        """
        all_findings: list[ScanFinding] = []
        errors: list[str] = []

        for scanner in self.scanners:
            try:
                result = scanner.scan()
                all_findings.extend(result.findings)
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"{scanner.__class__.__name__}: {str(e)}")

        return ScanResult(
            findings=all_findings,
            total_count=len(all_findings),
            severity_counts={
                "critical": len([f for f in all_findings if f.severity == "critical"]),
                "high": len([f for f in all_findings if f.severity == "high"]),
                "medium": len([f for f in all_findings if f.severity == "medium"]),
                "low": len([f for f in all_findings if f.severity == "low"]),
            },
            errors=errors,
        )


def run_security_scan(
    target_path: str = ".",
    scan_dependencies: bool = True,
    scan_secrets: bool = True,
    scan_code: bool = True,
) -> ScanResult:
    """Run a comprehensive security scan.

    This is the main entry point for security scanning.

    Args:
        target_path: Directory to scan
        scan_dependencies: Check for vulnerable dependencies
        scan_secrets: Check for leaked secrets
        scan_code: Run static analysis

    Returns:
        ScanResult with all findings

    Example:
        >>> from codewarden.scanners import run_security_scan
        >>> result = run_security_scan("./my_project")
        >>> print(f"Found {result.total_count} issues")
        >>> for finding in result.findings:
        ...     print(f"[{finding.severity}] {finding.title}")
    """
    audit = SecurityAudit(
        scan_dependencies=scan_dependencies,
        scan_secrets=scan_secrets,
        scan_code=scan_code,
        target_path=target_path,
    )
    return audit.run()
