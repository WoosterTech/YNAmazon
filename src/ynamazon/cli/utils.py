import datetime as dt
import enum
from importlib.metadata import PackageNotFoundError, metadata
from typing import Annotated, Any, ClassVar, Self

import requests
import typer

# used as a "test" that the repo URL is valid
from furl import furl  # type: ignore[import-untyped]
from loguru import logger
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)
from rich.console import Console


class GithubRepoUrl(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    url: AnyUrl
    _furl_obj: furl = furl("")
    _api_host: ClassVar[furl] = furl("https://api.github.com")

    @property
    def owner(self) -> str:
        """Get the owner of the repository."""
        return self._furl_obj.path.segments[0]

    @property
    def repo_name(self) -> str:
        """Get the name of the repository."""
        return self._furl_obj.path.segments[1]

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, value: Any) -> Any:
        if isinstance(value, furl):
            return str(value)
        return value

    @model_validator(mode="after")
    def set_furl_object(self) -> Self:
        """Set the furl object for the URL."""
        self._furl_obj = furl(url=self.url)
        return self

    @property
    def api_workflows(self) -> furl:
        """Get the API URL for workflows."""
        return (
            self._api_host
            / "repos"
            / self.owner
            / self.repo_name
            / "actions"
            / "workflows"
        )


def get_label_link(url: str) -> tuple[str, furl]:
    try:
        label, url = map(str.strip, url.split(", ", 1))
        return label, furl(url)
    except ValueError as e:
        raise ValueError(f"Invalid URL format: {url}") from e


def get_github_url(package_name: str) -> GithubRepoUrl:
    try:
        dist = metadata(package_name)
        urls = dist.get_all("Project-URL") or []

        for url in urls:
            label, link = get_label_link(url)
            logger.debug(f"Label: {label}, Link: {link}")
            if any(name in label.lower() for name in ["github", "source"]):
                return GithubRepoUrl(url=link)
        msg = f"Package '{package_name}' does not have a repository URL."
    except PackageNotFoundError:
        msg = f"Package '{package_name}' not found."

    raise ValueError(msg)


def parse_github_repo(value: str) -> GithubRepoUrl:
    if isinstance(value, GithubRepoUrl):
        return value
    try:
        return GithubRepoUrl(url=value)  # type: ignore[arg-type]
    except ValueError as e:
        raise typer.BadParameter(f"Invalid GitHub URL: {e}") from e


WORKFLOW_FILENAME = "integration.yml"


class ResponseBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


class WorkflowConclusion(enum.StrEnum):
    SUCCESS = enum.auto()
    FAILURE = enum.auto()
    CANCELLED = enum.auto()


class WorkflowStatus(enum.StrEnum):
    QUEUED = enum.auto()
    IN_PROGRESS = enum.auto()
    COMPLETED = enum.auto()
    ACTION_REQUIRED = enum.auto()


class WorkflowEvent(enum.StrEnum):
    PUSH = enum.auto()
    PULL_REQUEST = enum.auto()
    WORKFLOW_DISPATCH = enum.auto()
    SCHEDULE = enum.auto()
    MANUAL = enum.auto()
    OTHER = enum.auto()
    RELEASE = enum.auto()


class WorkflowReference(ResponseBase):
    path: str
    sha: str
    ref: str


class Person(ResponseBase):
    name: str
    email: EmailStr


class Actor(ResponseBase):
    login: str
    id: int
    type: str
    avatar_url: AnyUrl
    url: AnyUrl
    html_url: AnyUrl


class Commit(ResponseBase):
    id: str
    tree_id: str
    message: str
    timestamp: dt.datetime
    author: Person
    committer: Person


class WorkflowRun(ResponseBase):
    id: int
    name: str
    node_id: str
    head_branch: str
    head_sha: str
    path: str
    display_title: str
    run_number: int
    event: WorkflowEvent | str
    status: str
    conclusion: str
    workflow_id: int
    url: AnyUrl
    html_url: AnyUrl
    pull_requests: list[AnyUrl]
    created_at: dt.datetime
    updated_at: dt.datetime
    actor: Actor
    run_attempt: int
    referenced_workflows: list[WorkflowReference]
    run_started_at: dt.datetime
    triggering_actor: Actor
    previous_attempt_url: AnyUrl | None
    head_commit: Commit

    @property
    def passed(self) -> bool:
        """Check if the workflow run passed."""
        return self.conclusion == "success" and self.status == "completed"


class WorkflowResponse(ResponseBase):
    total_count: int
    workflow_runs: list[WorkflowRun] = []

    def get_latest_run(self) -> WorkflowRun:
        """Get the latest workflow run.

        Returns the first workflow run in the list.

        Raises ValueError if no workflow runs are found.
        """
        if self.workflow_runs:
            return self.workflow_runs[0]
        raise ValueError("No workflow runs found.")


def build_workflow_url(
    repo_url: GithubRepoUrl, filename: str = WORKFLOW_FILENAME
) -> furl:
    """Build the URL to the GitHub Actions workflow."""
    return repo_url.api_workflows / filename


def get_workflow_runs(repo_url: GithubRepoUrl, filename: str = WORKFLOW_FILENAME):
    """Get the workflow runs for the given repository URL."""
    workflow_url = build_workflow_url(repo_url, filename) / "runs"
    logger.debug(f"Workflow URL: {workflow_url}")
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(workflow_url.url, headers=headers)
    response.raise_for_status()

    return WorkflowResponse.model_validate(response.json())


app = typer.Typer(rich_markup_mode="rich")


@app.command()
def check_amazon_orders(
    repo_url: Annotated[
        GithubRepoUrl,
        typer.Argument(
            parser=parse_github_repo,
            default_factory=lambda: get_github_url("amazon-orders"),
        ),
    ],
    filename: Annotated[
        str,
        typer.Option("--filename", "-f", help="Name of the workflow file to check."),
    ] = WORKFLOW_FILENAME,
):
    """Check the Amazon orders repository integration test status."""
    console = Console()
    try:
        console.print(f"[bold cyan]Repository URL:[/] {repo_url.url}")
        workflow_response = get_workflow_runs(repo_url, filename)
        latest_run = workflow_response.get_latest_run()
        if latest_run.passed:
            console.print("✅ [bold green]Workflow passed on the latest run.[/]")
        else:
            console.print("❌ [bold yellow]Workflow failed on the latest run.[/]")
    except ValueError as e:
        console.print(f"⚠️  [bold red]Could not fetch workflow runs: {e}[/]")
