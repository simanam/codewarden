"""Deployment Tracker for CI/CD evidence collection.

Provides automatic deployment tracking for various CI/CD platforms.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from codewarden.client import CodeWardenClient
from codewarden.evidence.collector import EvidenceCollector


@dataclass
class DeploymentInfo:
    """Information about a deployment."""

    version: str
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    environment: str = "production"
    deployer: Optional[str] = None
    build_url: Optional[str] = None
    build_number: Optional[str] = None
    repository: Optional[str] = None
    ci_platform: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "success"  # success, failed, cancelled


class DeploymentTracker:
    """Track deployments and send evidence to CodeWarden.

    Automatically detects CI/CD environment and extracts deployment
    information for compliance logging.

    Supported platforms:
    - GitHub Actions
    - GitLab CI
    - CircleCI
    - Jenkins
    - Bitbucket Pipelines
    - Azure DevOps
    - Travis CI

    Example:
        >>> from codewarden.evidence import DeploymentTracker
        >>> tracker = DeploymentTracker()
        >>>
        >>> # Auto-detect and log deployment
        >>> tracker.track_deployment("1.2.3")
        >>>
        >>> # Or with manual info
        >>> tracker.track_deployment(
        ...     version="1.2.3",
        ...     environment="staging",
        ...     deployer="deploy-bot"
        ... )
    """

    def __init__(
        self,
        client: Optional[CodeWardenClient] = None,
        auto_detect: bool = True,
    ):
        """Initialize deployment tracker.

        Args:
            client: CodeWarden client instance
            auto_detect: Auto-detect CI/CD environment
        """
        self._collector = EvidenceCollector(client)
        self._auto_detect = auto_detect
        self._ci_info: Optional[DeploymentInfo] = None

        if auto_detect:
            self._detect_ci_environment()

    def _detect_ci_environment(self) -> None:
        """Detect CI/CD platform and extract info."""
        # GitHub Actions
        if os.environ.get("GITHUB_ACTIONS") == "true":
            self._ci_info = self._parse_github_actions()
            return

        # GitLab CI
        if os.environ.get("GITLAB_CI") == "true":
            self._ci_info = self._parse_gitlab_ci()
            return

        # CircleCI
        if os.environ.get("CIRCLECI") == "true":
            self._ci_info = self._parse_circleci()
            return

        # Jenkins
        if os.environ.get("JENKINS_URL"):
            self._ci_info = self._parse_jenkins()
            return

        # Bitbucket Pipelines
        if os.environ.get("BITBUCKET_BUILD_NUMBER"):
            self._ci_info = self._parse_bitbucket()
            return

        # Azure DevOps
        if os.environ.get("SYSTEM_TEAMPROJECT"):
            self._ci_info = self._parse_azure_devops()
            return

        # Travis CI
        if os.environ.get("TRAVIS") == "true":
            self._ci_info = self._parse_travis()
            return

    def _parse_github_actions(self) -> DeploymentInfo:
        """Parse GitHub Actions environment."""
        return DeploymentInfo(
            version=os.environ.get("GITHUB_REF_NAME", "unknown"),
            commit_sha=os.environ.get("GITHUB_SHA"),
            branch=os.environ.get("GITHUB_REF_NAME"),
            deployer=os.environ.get("GITHUB_ACTOR"),
            repository=os.environ.get("GITHUB_REPOSITORY"),
            build_number=os.environ.get("GITHUB_RUN_NUMBER"),
            build_url=(
                f"https://github.com/{os.environ.get('GITHUB_REPOSITORY')}"
                f"/actions/runs/{os.environ.get('GITHUB_RUN_ID')}"
            ),
            ci_platform="github_actions",
        )

    def _parse_gitlab_ci(self) -> DeploymentInfo:
        """Parse GitLab CI environment."""
        return DeploymentInfo(
            version=os.environ.get("CI_COMMIT_TAG") or os.environ.get("CI_COMMIT_REF_NAME", "unknown"),
            commit_sha=os.environ.get("CI_COMMIT_SHA"),
            branch=os.environ.get("CI_COMMIT_REF_NAME"),
            deployer=os.environ.get("GITLAB_USER_LOGIN"),
            environment=os.environ.get("CI_ENVIRONMENT_NAME", "production"),
            repository=os.environ.get("CI_PROJECT_PATH"),
            build_number=os.environ.get("CI_PIPELINE_ID"),
            build_url=os.environ.get("CI_PIPELINE_URL"),
            ci_platform="gitlab_ci",
        )

    def _parse_circleci(self) -> DeploymentInfo:
        """Parse CircleCI environment."""
        return DeploymentInfo(
            version=os.environ.get("CIRCLE_TAG") or os.environ.get("CIRCLE_BRANCH", "unknown"),
            commit_sha=os.environ.get("CIRCLE_SHA1"),
            branch=os.environ.get("CIRCLE_BRANCH"),
            deployer=os.environ.get("CIRCLE_USERNAME"),
            repository=f"{os.environ.get('CIRCLE_PROJECT_USERNAME')}/{os.environ.get('CIRCLE_PROJECT_REPONAME')}",
            build_number=os.environ.get("CIRCLE_BUILD_NUM"),
            build_url=os.environ.get("CIRCLE_BUILD_URL"),
            ci_platform="circleci",
        )

    def _parse_jenkins(self) -> DeploymentInfo:
        """Parse Jenkins environment."""
        return DeploymentInfo(
            version=os.environ.get("BUILD_TAG", "unknown"),
            commit_sha=os.environ.get("GIT_COMMIT"),
            branch=os.environ.get("GIT_BRANCH"),
            deployer=os.environ.get("BUILD_USER"),
            build_number=os.environ.get("BUILD_NUMBER"),
            build_url=os.environ.get("BUILD_URL"),
            ci_platform="jenkins",
        )

    def _parse_bitbucket(self) -> DeploymentInfo:
        """Parse Bitbucket Pipelines environment."""
        return DeploymentInfo(
            version=os.environ.get("BITBUCKET_TAG") or os.environ.get("BITBUCKET_BRANCH", "unknown"),
            commit_sha=os.environ.get("BITBUCKET_COMMIT"),
            branch=os.environ.get("BITBUCKET_BRANCH"),
            deployer=os.environ.get("BITBUCKET_STEP_TRIGGERER_UUID"),
            repository=os.environ.get("BITBUCKET_REPO_FULL_NAME"),
            build_number=os.environ.get("BITBUCKET_BUILD_NUMBER"),
            build_url=(
                f"https://bitbucket.org/{os.environ.get('BITBUCKET_REPO_FULL_NAME')}"
                f"/addon/pipelines/home#!/results/{os.environ.get('BITBUCKET_BUILD_NUMBER')}"
            ),
            ci_platform="bitbucket",
        )

    def _parse_azure_devops(self) -> DeploymentInfo:
        """Parse Azure DevOps environment."""
        return DeploymentInfo(
            version=os.environ.get("BUILD_SOURCEVERSION", "unknown")[:7],
            commit_sha=os.environ.get("BUILD_SOURCEVERSION"),
            branch=os.environ.get("BUILD_SOURCEBRANCHNAME"),
            deployer=os.environ.get("BUILD_REQUESTEDFOR"),
            repository=os.environ.get("BUILD_REPOSITORY_NAME"),
            build_number=os.environ.get("BUILD_BUILDNUMBER"),
            build_url=(
                f"{os.environ.get('SYSTEM_TEAMFOUNDATIONCOLLECTIONURI')}"
                f"{os.environ.get('SYSTEM_TEAMPROJECT')}/_build/results"
                f"?buildId={os.environ.get('BUILD_BUILDID')}"
            ),
            ci_platform="azure_devops",
        )

    def _parse_travis(self) -> DeploymentInfo:
        """Parse Travis CI environment."""
        return DeploymentInfo(
            version=os.environ.get("TRAVIS_TAG") or os.environ.get("TRAVIS_BRANCH", "unknown"),
            commit_sha=os.environ.get("TRAVIS_COMMIT"),
            branch=os.environ.get("TRAVIS_BRANCH"),
            deployer=os.environ.get("TRAVIS_COMMIT_AUTHOR"),
            repository=os.environ.get("TRAVIS_REPO_SLUG"),
            build_number=os.environ.get("TRAVIS_BUILD_NUMBER"),
            build_url=os.environ.get("TRAVIS_BUILD_WEB_URL"),
            ci_platform="travis_ci",
        )

    def get_ci_info(self) -> Optional[DeploymentInfo]:
        """Get detected CI/CD information.

        Returns:
            DeploymentInfo if in a CI environment, None otherwise
        """
        return self._ci_info

    def is_ci_environment(self) -> bool:
        """Check if running in a CI/CD environment.

        Returns:
            True if CI/CD environment detected
        """
        return self._ci_info is not None

    def track_deployment(
        self,
        version: Optional[str] = None,
        environment: Optional[str] = None,
        deployer: Optional[str] = None,
        status: str = "success",
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Track a deployment event.

        Uses auto-detected CI info if available, with manual overrides.

        Args:
            version: Version being deployed (auto-detected if None)
            environment: Target environment (default: production)
            deployer: Who triggered the deployment
            status: Deployment status (success, failed, cancelled)
            metadata: Additional metadata

        Returns:
            Event ID if successful

        Example:
            >>> tracker.track_deployment("1.2.3", environment="production")
        """
        # Merge auto-detected info with provided values
        info = self._ci_info

        return self._collector.log_deployment(
            version=version or (info.version if info else "unknown"),
            commit_sha=info.commit_sha if info else None,
            deployer=deployer or (info.deployer if info else None),
            environment=environment or (info.environment if info else "production"),
            branch=info.branch if info else None,
            build_url=info.build_url if info else None,
            metadata={
                "ci_platform": info.ci_platform if info else None,
                "repository": info.repository if info else None,
                "build_number": info.build_number if info else None,
                "status": status,
                **(metadata or {}),
            },
        )

    def track_deployment_start(
        self,
        version: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> "DeploymentContext":
        """Start tracking a deployment with timing.

        Returns a context manager that tracks deployment duration.

        Args:
            version: Version being deployed
            environment: Target environment

        Returns:
            DeploymentContext for use with 'with' statement

        Example:
            >>> with tracker.track_deployment_start("1.2.3") as deploy:
            ...     # Do deployment work
            ...     pass
            >>> # Deployment automatically logged when context exits
        """
        return DeploymentContext(
            tracker=self,
            version=version,
            environment=environment,
        )


class DeploymentContext:
    """Context manager for tracking deployment duration."""

    def __init__(
        self,
        tracker: DeploymentTracker,
        version: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        self._tracker = tracker
        self._version = version
        self._environment = environment
        self._start_time: Optional[datetime] = None
        self._status = "success"
        self._error: Optional[str] = None

    def __enter__(self) -> "DeploymentContext":
        self._start_time = datetime.now(timezone.utc)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - self._start_time).total_seconds() * 1000)

        if exc_type is not None:
            self._status = "failed"
            self._error = str(exc_val)

        self._tracker.track_deployment(
            version=self._version,
            environment=self._environment,
            status=self._status,
            metadata={
                "duration_ms": duration_ms,
                "started_at": self._start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "error": self._error,
            },
        )

        return False  # Don't suppress exceptions

    def fail(self, reason: str) -> None:
        """Mark deployment as failed.

        Args:
            reason: Reason for failure
        """
        self._status = "failed"
        self._error = reason

    def cancel(self, reason: Optional[str] = None) -> None:
        """Mark deployment as cancelled.

        Args:
            reason: Reason for cancellation
        """
        self._status = "cancelled"
        self._error = reason
