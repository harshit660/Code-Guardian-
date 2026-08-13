from dataclasses import dataclass

import httpx

from app.analysis.contracts import SourceFile
from app.core.config import get_settings


class GitHubGatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepositorySnapshot:
    commit_sha: str | None
    files: list[SourceFile]


class GitHubGateway:
    def __init__(self) -> None:
        settings = get_settings()
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        self.client = httpx.Client(base_url=settings.github_api_url, headers=headers, timeout=20.0)

    def branches(self, owner: str, repository: str) -> list[str]:
        response = self.client.get(f"/repos/{owner}/{repository}/branches", params={"per_page": 100})
        self._check(response)
        return [item["name"] for item in response.json()]

    def snapshot(self, owner: str, repository: str, branch: str) -> RepositorySnapshot:
        commit = self.client.get(f"/repos/{owner}/{repository}/commits/{branch}")
        self._check(commit)
        commit_data = commit.json()
        sha = commit_data["sha"]
        tree_sha = commit_data["commit"]["tree"]["sha"]
        tree = self.client.get(f"/repos/{owner}/{repository}/git/trees/{tree_sha}", params={"recursive": "1"})
        self._check(tree)
        entries = tree.json().get("tree", [])
        files: list[SourceFile] = []
        for entry in entries:
            if entry.get("type") != "blob" or entry.get("size", 0) > 750_000 or len(files) >= 500:
                continue
            path = entry["path"]
            if any(part in path for part in ("node_modules/", ".git/", "vendor/", "dist/", "build/")):
                continue
            content = self.client.get(f"/repos/{owner}/{repository}/contents/{path}", params={"ref": sha})
            if content.status_code != 200:
                continue
            data = content.json()
            if data.get("encoding") != "base64":
                continue
            import base64

            try:
                decoded = base64.b64decode(data["content"]).decode("utf-8")
            except UnicodeDecodeError:
                continue
            files.append(SourceFile(path, decoded))
        return RepositorySnapshot(sha, files)

    def submit_review(self, owner: str, repository: str, pull_number: int, comments: list[dict[str, object]]) -> None:
        response = self.client.post(
            f"/repos/{owner}/{repository}/pulls/{pull_number}/reviews",
            json={"event": "COMMENT", "body": "CodeGuardian automated analysis", "comments": comments},
        )
        self._check(response)

    @staticmethod
    def _check(response: httpx.Response) -> None:
        if response.is_error:
            detail = response.json().get("message", response.text) if response.content else "Unknown GitHub API error"
            raise GitHubGatewayError(f"GitHub API error {response.status_code}: {detail}")

