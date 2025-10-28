"""Shared container registry configuration for CI scaffolding.

This module provides unified registry configuration that works across multiple
CI platforms (GitHub Actions, GitLab CI, etc.). Each registry has platform-specific
fragment paths and secrets hint formatting.
"""

from pathlib import Path
from typing import Callable, NamedTuple, Optional

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class ContainerRegistryInfo(NamedTuple):
    """Information about a container registry and its CI integration.

    Attributes:
        name: Human-readable registry name
        match: Function to match registry URLs
        github_fragment: Path to GitHub Actions login fragment
        gitlab_fragment: Path to GitLab CI login fragment
        github_secrets: List of GitHub secrets hints (formatted for gh CLI)
        gitlab_secrets: List of GitLab secrets hints (formatted for UI)
    """

    name: str
    match: Callable[[str], bool]
    github_fragment: Path
    gitlab_fragment: Optional[Path]
    github_secrets: list[str]
    gitlab_secrets: list[str]


# Unified registry configuration
CONTAINER_REGISTRIES = [
    ContainerRegistryInfo(
        name="ECR",
        match=lambda url: ".ecr." in url or url.startswith("ecr."),
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "ecr-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "ecr-login-fragment.yml",
        github_secrets=[
            'gh secret set AWS_ACCESS_KEY_ID --body "(your AWS access key ID)"',
            'gh secret set AWS_SECRET_ACCESS_KEY --body "(your AWS secret access key)"',
            'gh secret set AWS_REGION --body "(your AWS region)"',
        ],
        gitlab_secrets=[
            "AWS_ACCESS_KEY_ID - Your AWS access key ID",
            "AWS_SECRET_ACCESS_KEY - Your AWS secret access key",
            "AWS_REGION - Your AWS region (e.g., us-east-1)",
        ],
    ),
    ContainerRegistryInfo(
        name="DockerHub",
        match=lambda url: "docker.io" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "dockerhub-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR
        / "gitlab_registry_fragments"
        / "dockerhub-login-fragment.yml",
        github_secrets=[
            'gh secret set DOCKERHUB_USERNAME --body "(your DockerHub username)"',
            'gh secret set DOCKERHUB_TOKEN --body "(your DockerHub token)"',
        ],
        gitlab_secrets=[
            "DOCKERHUB_USERNAME - Your DockerHub username",
            "DOCKERHUB_TOKEN - Your DockerHub access token",
        ],
    ),
    ContainerRegistryInfo(
        name="GitHub Container Registry",
        match=lambda url: "ghcr.io" in url,
        github_fragment=TEMPLATES_DIR
        / "registry_fragments"
        / "github-container-registry-login-fragment.yaml",
        gitlab_fragment=None,  # Not typically used in GitLab
        github_secrets=[],
        gitlab_secrets=[],
    ),
    ContainerRegistryInfo(
        name="GitLab Container Registry",
        match=lambda url: "registry.gitlab.com" in url or "gitlab.com" in url,
        github_fragment=None,  # Not used in GitHub
        gitlab_fragment=TEMPLATES_DIR
        / "gitlab_registry_fragments"
        / "gitlab-container-registry-login-fragment.yml",
        github_secrets=[],
        gitlab_secrets=[],
    ),
    ContainerRegistryInfo(
        name="Azure Container Registry",
        match=lambda url: "azurecr.io" in url,
        github_fragment=TEMPLATES_DIR
        / "registry_fragments"
        / "azure-container-registry-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR
        / "gitlab_registry_fragments"
        / "azure-container-registry-login-fragment.yml",
        github_secrets=[
            'gh secret set AZURE_CLIENT_ID --body "(your Azure client ID)"',
            'gh secret set AZURE_CLIENT_SECRET --body "(your Azure client secret)"',
        ],
        gitlab_secrets=[
            "AZURE_CLIENT_ID - Your Azure client ID",
            "AZURE_CLIENT_SECRET - Your Azure client secret",
            "AZURE_TENANT_ID - Your Azure tenant ID",
        ],
    ),
    ContainerRegistryInfo(
        name="Google Container Registry",
        match=lambda url: "gcr.io" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "gcr-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "gcr-login-fragment.yml",
        github_secrets=[
            'gh secret set GCR_JSON_KEY --body "(your GCR JSON key)"',
        ],
        gitlab_secrets=[
            "GCR_JSON_KEY - Your GCR service account JSON key",
        ],
    ),
]


def get_registry_for_url(url: str) -> Optional[ContainerRegistryInfo]:
    """Get registry info for a given URL.

    Args:
        url: Container registry URL

    Returns:
        ContainerRegistryInfo if a matching registry is found, None otherwise
    """
    for registry in CONTAINER_REGISTRIES:
        if registry.match(url):
            return registry
    return None


def get_secrets_hints_for_urls(registry_urls: list[str], platform: str) -> list[str]:
    """Get secrets hints for a list of registry URLs.

    Args:
        registry_urls: List of container registry URLs
        platform: Either "github" or "gitlab"

    Returns:
        List of secrets hints for the specified platform
    """
    secrets_hints = []
    seen_registries = set()

    for url in registry_urls:
        registry = get_registry_for_url(url)
        if registry and registry.name not in seen_registries:
            seen_registries.add(registry.name)
            hints = registry.github_secrets if platform == "github" else registry.gitlab_secrets
            secrets_hints.extend(hints)

    return secrets_hints
