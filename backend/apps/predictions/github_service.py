import logging
import requests
from django.conf import settings
from .models import PullRequestMetric, ReviewerAvailability

logger = logging.getLogger(__name__)


class GitHubPRService:
    """
    Service layer to interact with GitHub API for PR metadata & Reviewer metrics.
    """

    def __init__(self, token=None):
        self.token = token
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def fetch_pr_data(self, owner: str, repo: str, pr_number: int) -> dict:
        """
        Fetches PR metadata from GitHub API or returns simulated PR metrics with logged fallback.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        if self.token:
            try:
                res = requests.get(url, headers=self.headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "pr_number": data.get("number"),
                        "title": data.get("title", ""),
                        "author": data.get("user", {}).get("login", "unknown"),
                        "additions": data.get("additions", 0),
                        "deletions": data.get("deletions", 0),
                        "changed_files": data.get("changed_files", 0),
                        "requested_reviewers": [r.get("login") for r in data.get("requested_reviewers", [])],
                        "is_simulated": False,
                    }
                else:
                    logger.warning("GitHub API returned status code %s for PR #%s. Operating in degraded fallback mode.", res.status_code, pr_number)
            except Exception as exc:
                logger.warning("GitHub API request failed for PR #%s: %s. Operating in degraded fallback mode.", pr_number, exc)

        logger.info("Using simulated fallback PR data for PR #%s", pr_number)
        return {
            "pr_number": pr_number,
            "title": f"Feature Implementation #{pr_number}",
            "author": "contributor",
            "additions": 150 + (pr_number * 10) % 500,
            "deletions": 30 + (pr_number * 5) % 200,
            "changed_files": 4 + (pr_number % 8),
            "requested_reviewers": ["maintainer-1"],
            "is_simulated": True,
        }

    def sync_pr_metric(self, pr_data: dict, assigned_reviewer_username: str = None) -> PullRequestMetric:
        """
        Upserts PR metric in database without clearing existing reviewer assignment if none provided.
        """
        defaults = {
            "title": pr_data.get("title", "Untitled PR"),
            "author": pr_data.get("author", "unknown"),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "changed_files": pr_data.get("changed_files", 0),
            "status": "OPEN",
        }

        if assigned_reviewer_username:
            reviewer, _ = ReviewerAvailability.objects.get_or_create(
                reviewer_username=assigned_reviewer_username,
                defaults={"current_workload": 1, "activity_score": 0.8}
            )
            defaults["assigned_reviewer"] = reviewer

        pr_metric, created = PullRequestMetric.objects.get_or_create(
            pr_number=pr_data["pr_number"],
            defaults=defaults,
        )

        if not created:
            for key, val in defaults.items():
                setattr(pr_metric, key, val)
            pr_metric.save()

        return pr_metric
