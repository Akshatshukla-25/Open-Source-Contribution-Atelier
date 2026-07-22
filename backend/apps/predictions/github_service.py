import requests
from django.conf import settings
from .models import PullRequestMetric, ReviewerAvailability


class GitHubPRService:
    """
    Service layer to interact with GitHub API for PR metadata & Reviewer metrics.
    """

    def __init__(self, token=None):
        self.token = token
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def fetch_pr_data(self, owner: str, repo: str, pr_number: int) -> dict:
        """
        Fetches PR metadata from GitHub API or returns simulated PR metrics.
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
                    }
            except Exception:
                pass

        # Fallback simulated data for offline/test environments
        return {
            "pr_number": pr_number,
            "title": f"Feature Implementation #{pr_number}",
            "author": "contributor",
            "additions": 150 + (pr_number * 10) % 500,
            "deletions": 30 + (pr_number * 5) % 200,
            "changed_files": 4 + (pr_number % 8),
            "requested_reviewers": ["maintainer-1"],
        }

    def sync_pr_metric(self, pr_data: dict, assigned_reviewer_username: str = None) -> PullRequestMetric:
        """
        Upserts PR metric in database.
        """
        reviewer = None
        if assigned_reviewer_username:
            reviewer, _ = ReviewerAvailability.objects.get_or_create(
                reviewer_username=assigned_reviewer_username,
                defaults={"current_workload": 1, "activity_score": 0.8}
            )

        pr_metric, _ = PullRequestMetric.objects.update_or_create(
            pr_number=pr_data["pr_number"],
            defaults={
                "title": pr_data.get("title", "Untitled PR"),
                "author": pr_data.get("author", "unknown"),
                "assigned_reviewer": reviewer,
                "additions": pr_data.get("additions", 0),
                "deletions": pr_data.get("deletions", 0),
                "changed_files": pr_data.get("changed_files", 0),
                "status": "OPEN",
            }
        )
        return pr_metric
