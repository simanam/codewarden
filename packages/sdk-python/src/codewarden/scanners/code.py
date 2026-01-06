"""Static code analysis scanner using Bandit."""

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from codewarden.scanners.base import BaseScannerModule, ScanResult


class CodeScanner(BaseScannerModule):
    """Scan Python code for security issues using Bandit.

    Bandit is a tool designed to find common security issues in Python code.
    It processes each file, builds an AST, and runs plugins against the AST nodes.

    Example:
        >>> scanner = CodeScanner(target_path="./src")
        >>> result = scanner.scan()
        >>> for finding in result.findings:
        ...     print(f"{finding.severity}: {finding.title} in {finding.file_path}")
    """

    # CWE mappings for common Bandit test IDs
    CWE_MAPPINGS: dict[str, str] = {
        "B101": "CWE-703",  # assert_used - Improper Check or Handling of Exceptional Conditions
        "B102": "CWE-78",   # exec_used - OS Command Injection
        "B103": "CWE-732",  # set_bad_file_permissions - Incorrect Permission Assignment
        "B104": "CWE-200",  # hardcoded_bind_all_interfaces - Information Exposure
        "B105": "CWE-259",  # hardcoded_password_string - Use of Hard-coded Password
        "B106": "CWE-259",  # hardcoded_password_funcarg - Use of Hard-coded Password
        "B107": "CWE-259",  # hardcoded_password_default - Use of Hard-coded Password
        "B108": "CWE-377",  # hardcoded_tmp_directory - Insecure Temporary File
        "B110": "CWE-703",  # try_except_pass - Improper Handling of Exceptional Conditions
        "B112": "CWE-703",  # try_except_continue - Improper Handling of Exceptional Conditions
        "B201": "CWE-94",   # flask_debug_true - Code Injection
        "B301": "CWE-502",  # pickle - Deserialization of Untrusted Data
        "B302": "CWE-78",   # marshal - OS Command Injection
        "B303": "CWE-327",  # md5/sha1 - Use of Broken Crypto Algorithm
        "B304": "CWE-327",  # des - Use of Broken Crypto Algorithm
        "B305": "CWE-327",  # cipher_modes - Use of Broken Crypto Algorithm
        "B306": "CWE-377",  # mktemp_q - Insecure Temporary File
        "B307": "CWE-78",   # eval - OS Command Injection
        "B308": "CWE-611",  # mark_safe - XML External Entity Reference
        "B310": "CWE-918",  # urllib_urlopen - Server-Side Request Forgery
        "B311": "CWE-330",  # random - Use of Insufficiently Random Values
        "B312": "CWE-295",  # telnetlib - Improper Certificate Validation
        "B313": "CWE-611",  # xml_bad_cElementTree - XML External Entity Reference
        "B314": "CWE-611",  # xml_bad_ElementTree - XML External Entity Reference
        "B315": "CWE-611",  # xml_bad_expatreader - XML External Entity Reference
        "B316": "CWE-611",  # xml_bad_expatbuilder - XML External Entity Reference
        "B317": "CWE-611",  # xml_bad_sax - XML External Entity Reference
        "B318": "CWE-611",  # xml_bad_minidom - XML External Entity Reference
        "B319": "CWE-611",  # xml_bad_pulldom - XML External Entity Reference
        "B320": "CWE-611",  # xml_bad_etree - XML External Entity Reference
        "B321": "CWE-295",  # ftplib - Improper Certificate Validation
        "B322": "CWE-78",   # input - OS Command Injection (Python 2)
        "B323": "CWE-295",  # unverified_context - Improper Certificate Validation
        "B324": "CWE-327",  # hashlib_new_insecure_functions - Use of Broken Crypto
        "B401": "CWE-295",  # import_telnetlib - Improper Certificate Validation
        "B402": "CWE-295",  # import_ftplib - Improper Certificate Validation
        "B403": "CWE-502",  # import_pickle - Deserialization of Untrusted Data
        "B404": "CWE-78",   # import_subprocess - OS Command Injection
        "B405": "CWE-611",  # import_xml_etree - XML External Entity Reference
        "B406": "CWE-611",  # import_xml_sax - XML External Entity Reference
        "B407": "CWE-611",  # import_xml_expat - XML External Entity Reference
        "B408": "CWE-611",  # import_xml_minidom - XML External Entity Reference
        "B409": "CWE-611",  # import_xml_pulldom - XML External Entity Reference
        "B410": "CWE-611",  # import_lxml - XML External Entity Reference
        "B411": "CWE-611",  # import_xmlrpclib - XML External Entity Reference
        "B412": "CWE-78",   # import_httpoxy - OS Command Injection
        "B413": "CWE-327",  # import_pycrypto - Use of Broken Crypto Algorithm
        "B501": "CWE-295",  # request_with_no_cert_validation - Improper Cert Validation
        "B502": "CWE-295",  # ssl_with_bad_version - Improper Certificate Validation
        "B503": "CWE-295",  # ssl_with_bad_defaults - Improper Certificate Validation
        "B504": "CWE-295",  # ssl_with_no_version - Improper Certificate Validation
        "B505": "CWE-327",  # weak_cryptographic_key - Use of Broken Crypto Algorithm
        "B506": "CWE-89",   # yaml_load - SQL Injection (similar pattern)
        "B507": "CWE-295",  # ssh_no_host_key_verification - Improper Cert Validation
        "B601": "CWE-78",   # paramiko_calls - OS Command Injection
        "B602": "CWE-78",   # subprocess_popen_with_shell_equals_true - OS Command Injection
        "B603": "CWE-78",   # subprocess_without_shell_equals_true - OS Command Injection
        "B604": "CWE-78",   # any_other_function_with_shell_equals_true - OS Command Injection
        "B605": "CWE-78",   # start_process_with_a_shell - OS Command Injection
        "B606": "CWE-78",   # start_process_with_no_shell - OS Command Injection
        "B607": "CWE-78",   # start_process_with_partial_path - OS Command Injection
        "B608": "CWE-89",   # hardcoded_sql_expressions - SQL Injection
        "B609": "CWE-78",   # linux_commands_wildcard_injection - OS Command Injection
        "B610": "CWE-78",   # django_extra_used - OS Command Injection
        "B611": "CWE-89",   # django_rawsql_used - SQL Injection
        "B701": "CWE-94",   # jinja2_autoescape_false - Code Injection
        "B702": "CWE-79",   # use_of_mako_templates - Cross-site Scripting
        "B703": "CWE-611",  # django_mark_safe - XML External Entity Reference
    }

    # Severity mapping from Bandit levels
    SEVERITY_MAP = {
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
    }

    # Confidence to severity boost
    CONFIDENCE_BOOST = {
        "HIGH": 1,
        "MEDIUM": 0,
        "LOW": -1,
    }

    def __init__(
        self,
        target_path: str = ".",
        severity_threshold: str = "low",
        confidence_threshold: str = "low",
        exclude_dirs: Optional[list[str]] = None,
        skip_tests: bool = False,
        config_file: Optional[str] = None,
        timeout: int = 300,
        config: Optional[dict] = None,
    ):
        """Initialize code scanner.

        Args:
            target_path: Directory or file to scan
            severity_threshold: Minimum severity to report (low, medium, high)
            confidence_threshold: Minimum confidence to report (low, medium, high)
            exclude_dirs: Directories to exclude from scanning
            skip_tests: Skip files in test directories
            config_file: Path to Bandit configuration file
            timeout: Command timeout in seconds
            config: Additional configuration
        """
        super().__init__(config)
        self.target_path = Path(target_path)
        self.severity_threshold = severity_threshold.upper()
        self.confidence_threshold = confidence_threshold.upper()
        self.exclude_dirs = exclude_dirs or ["venv", ".venv", "node_modules", ".git"]
        self.skip_tests = skip_tests
        self.config_file = config_file
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Bandit is available.

        Returns:
            True if bandit is installed and accessible
        """
        return shutil.which("bandit") is not None

    def scan(self) -> ScanResult:
        """Run Bandit security scan.

        Returns:
            ScanResult with code security findings
        """
        start_time = time.time()
        self._findings = []
        self._errors = []

        if not self.is_available():
            self._errors.append(
                "Bandit is not installed. Install with: pip install bandit"
            )
            return self._build_result(start_time)

        if not self.target_path.exists():
            self._errors.append(f"Target path does not exist: {self.target_path}")
            return self._build_result(start_time)

        try:
            result = self._run_bandit()
            if result:
                self._parse_results(result)
        except subprocess.TimeoutExpired:
            self._errors.append(f"Bandit scan timed out after {self.timeout} seconds")
        except subprocess.CalledProcessError as e:
            # Bandit returns non-zero exit codes when issues are found
            if e.stdout:
                self._parse_results(e.stdout)
            elif e.returncode != 1:
                self._errors.append(f"Bandit error (exit code {e.returncode}): {e.stderr or 'Unknown error'}")
        except json.JSONDecodeError as e:
            self._errors.append(f"Failed to parse Bandit output: {e}")
        except Exception as e:
            self._errors.append(f"Code scan error: {str(e)}")

        return self._build_result(start_time)

    def _run_bandit(self) -> Optional[str]:
        """Execute Bandit and return JSON output.

        Returns:
            JSON string output from Bandit or None
        """
        cmd = [
            "bandit",
            "-r",  # Recursive
            "-f", "json",  # JSON output format
            "-ll",  # Report only medium and above (configurable via threshold)
            str(self.target_path),
        ]

        # Add severity threshold
        severity_levels = {"LOW": "-l", "MEDIUM": "-ll", "HIGH": "-lll"}
        if self.severity_threshold in severity_levels:
            # Replace -ll with appropriate level
            cmd = [c for c in cmd if c not in ["-l", "-ll", "-lll"]]
            cmd.append(severity_levels[self.severity_threshold])

        # Add confidence threshold
        confidence_levels = {"LOW": "-i", "MEDIUM": "-ii", "HIGH": "-iii"}
        if self.confidence_threshold in confidence_levels:
            cmd.append(confidence_levels[self.confidence_threshold])

        # Add exclusions
        if self.exclude_dirs:
            cmd.extend(["--exclude", ",".join(self.exclude_dirs)])

        # Skip test files
        if self.skip_tests:
            cmd.append("--skip-tests")

        # Use config file if provided
        if self.config_file and Path(self.config_file).exists():
            cmd.extend(["-c", self.config_file])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=True,
        )

        return result.stdout

    def _parse_results(self, json_output: str) -> None:
        """Parse Bandit JSON output into findings.

        Args:
            json_output: JSON string from Bandit
        """
        try:
            data = json.loads(json_output)
        except json.JSONDecodeError:
            return

        results = data.get("results", [])

        for issue in results:
            test_id = issue.get("test_id", "")
            severity = self._map_severity(
                issue.get("issue_severity", "MEDIUM"),
                issue.get("issue_confidence", "MEDIUM"),
            )

            # Get relative file path
            file_path = issue.get("filename", "")
            try:
                if self.target_path.is_dir():
                    file_path = str(Path(file_path).relative_to(self.target_path))
            except ValueError:
                pass  # Keep absolute path if relative fails

            finding = self._create_finding(
                type="code",
                severity=severity,
                title=f"{test_id}: {issue.get('test_name', 'Security Issue')}",
                description=issue.get("issue_text", "Security issue detected"),
                file_path=file_path,
                line_number=issue.get("line_number"),
                column_number=issue.get("col_offset"),
                cwe_id=self.CWE_MAPPINGS.get(test_id),
                remediation=self._get_remediation(test_id, issue.get("test_name", "")),
                raw_data={
                    "test_id": test_id,
                    "test_name": issue.get("test_name"),
                    "issue_severity": issue.get("issue_severity"),
                    "issue_confidence": issue.get("issue_confidence"),
                    "line_range": issue.get("line_range", []),
                    "code": issue.get("code", ""),
                    "more_info": issue.get("more_info", ""),
                },
            )
            self._findings.append(finding)

        # Track metrics from Bandit output
        metrics = data.get("metrics", {})
        if metrics:
            total_loc = sum(m.get("loc", 0) for m in metrics.values() if isinstance(m, dict))
            if total_loc > 0 and self._findings:
                # Could add density metrics here
                pass

    def _map_severity(self, bandit_severity: str, bandit_confidence: str) -> str:
        """Map Bandit severity and confidence to our severity levels.

        Args:
            bandit_severity: Bandit severity (HIGH, MEDIUM, LOW)
            bandit_confidence: Bandit confidence (HIGH, MEDIUM, LOW)

        Returns:
            Mapped severity string
        """
        base_severity = self.SEVERITY_MAP.get(bandit_severity.upper(), "medium")

        # Boost severity based on confidence
        confidence_boost = self.CONFIDENCE_BOOST.get(bandit_confidence.upper(), 0)

        severity_order = ["low", "medium", "high", "critical"]
        current_idx = severity_order.index(base_severity)

        # Apply boost (high confidence + high severity = critical)
        if confidence_boost > 0 and current_idx >= 2:
            return "critical"

        return base_severity

    def _get_remediation(self, test_id: str, test_name: str) -> str:
        """Get remediation advice for a specific issue.

        Args:
            test_id: Bandit test ID (e.g., B101)
            test_name: Human-readable test name

        Returns:
            Remediation advice string
        """
        remediations = {
            "B101": "Remove assert statements from production code. Use proper exception handling instead.",
            "B102": "Avoid using exec(). Use safer alternatives like importlib for dynamic imports.",
            "B103": "Use more restrictive file permissions (e.g., 0o600 for sensitive files).",
            "B104": "Bind to specific IP addresses instead of 0.0.0.0 in production.",
            "B105": "Use environment variables or a secrets manager instead of hardcoded passwords.",
            "B106": "Use environment variables or a secrets manager instead of hardcoded passwords.",
            "B107": "Use environment variables or a secrets manager instead of hardcoded passwords.",
            "B108": "Use tempfile.mkstemp() or tempfile.TemporaryDirectory() instead of hardcoded tmp paths.",
            "B110": "Handle exceptions explicitly instead of using bare except with pass.",
            "B112": "Handle exceptions explicitly instead of using bare except with continue.",
            "B201": "Set debug=False in production Flask applications.",
            "B301": "Avoid pickle for untrusted data. Use JSON or other safe serialization formats.",
            "B303": "Use SHA-256 or stronger hashing algorithms instead of MD5/SHA1.",
            "B304": "Use AES or other modern encryption algorithms instead of DES.",
            "B306": "Use tempfile.mkstemp() instead of mktemp().",
            "B307": "Avoid eval(). Use ast.literal_eval() for safe evaluation of literals.",
            "B310": "Validate and sanitize URLs before making requests. Use allowlists for external URLs.",
            "B311": "Use secrets module instead of random for security-sensitive operations.",
            "B323": "Always verify SSL certificates. Create proper SSL contexts.",
            "B501": "Enable certificate verification in requests (verify=True).",
            "B502": "Use TLS 1.2 or higher. Avoid SSLv2, SSLv3, and TLS 1.0/1.1.",
            "B506": "Use yaml.safe_load() instead of yaml.load().",
            "B602": "Avoid shell=True in subprocess calls. Pass arguments as a list.",
            "B608": "Use parameterized queries instead of string formatting for SQL.",
            "B701": "Enable autoescape in Jinja2 templates to prevent XSS.",
        }

        return remediations.get(
            test_id,
            f"Review and fix the {test_name} security issue. "
            "Consult Bandit documentation for specific remediation guidance.",
        )

    def get_scan_metrics(self) -> dict:
        """Get additional scan metrics.

        Returns:
            Dictionary with scan metrics
        """
        if not self._findings:
            return {}

        # Count by test ID
        test_counts: dict[str, int] = {}
        for finding in self._findings:
            test_id = finding.raw_data.get("test_id", "unknown") if finding.raw_data else "unknown"
            test_counts[test_id] = test_counts.get(test_id, 0) + 1

        return {
            "total_findings": len(self._findings),
            "findings_by_test": test_counts,
            "unique_files": len(set(f.file_path for f in self._findings if f.file_path)),
        }
