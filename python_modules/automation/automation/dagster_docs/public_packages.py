"""Utilities for discovering public Dagster Python packages."""

from pathlib import Path

from dagster_shared.record import record


@record
class PublicPackage:
    """Information about a public Dagster package."""

    name: str  # Package name (e.g., "dagster", "dagster-aws")
    directory_name: str  # Directory name (e.g., "dagster", "dagster-aws")
    module_name: str  # Import name (e.g., "dagster", "dagster_aws")
    path: Path  # Full path to package directory


def get_public_dagster_packages(dagster_root: Path | None = None) -> list[PublicPackage]:
    """Get all public Dagster Python packages.

    This function returns all packages that are part of the public Dagster API,
    including top-level packages (dagster, dagster-pipes) and all
    Dagster libraries (dagster-*) found in the libraries/ directory.

    Args:
        dagster_root: Path to the Dagster repository root. If None, attempts to
                     find it relative to this file.

    Returns:
        List of PublicPackage objects representing all public packages.

    Raises:
        FileNotFoundError: If dagster_root doesn't exist or doesn't contain
                          the expected python_modules structure.
    """
    if dagster_root is None:
        # Find dagster root relative to this file
        dagster_root = Path(__file__).parent.parent.parent.parent.parent

    dagster_root = Path(dagster_root).resolve()
    python_modules_dir = dagster_root / "python_modules"

    if not python_modules_dir.exists():
        raise FileNotFoundError(f"python_modules directory not found at {python_modules_dir}")

    packages = []

    # Hardcoded list of top-level packages (dagster and dagster-pipes only)
    top_level_packages = ["dagster", "dagster-pipes"]

    for package_name in top_level_packages:
        package_dir = python_modules_dir / package_name
        if package_dir.exists() and (
            (package_dir / "setup.py").exists() or (package_dir / "pyproject.toml").exists()
        ):
            packages.append(
                PublicPackage(
                    name=package_name,
                    directory_name=package_name,
                    module_name=package_name.replace("-", "_"),
                    path=package_dir,
                )
            )

    # Add Dagster libraries from libraries/ directory
    libraries_dir = python_modules_dir / "libraries"
    if libraries_dir.exists():
        for lib_dir in libraries_dir.iterdir():
            if (
                lib_dir.is_dir()
                and lib_dir.name.startswith("dagster-")
                and not lib_dir.name.startswith(".")
                and ((lib_dir / "setup.py").exists() or (lib_dir / "pyproject.toml").exists())
            ):
                packages.append(
                    PublicPackage(
                        name=lib_dir.name,
                        directory_name=lib_dir.name,
                        module_name=lib_dir.name.replace("-", "_"),
                        path=lib_dir,
                    )
                )

    # Sort by name for consistent ordering
    packages.sort(key=lambda p: p.name)

    return packages


def get_top_level_packages() -> list[str]:
    """Get just the top-level Dagster package names (dagster and dagster-pipes).

    Returns:
        List of top-level package names: ["dagster", "dagster-pipes"]
    """
    packages = get_public_dagster_packages()
    top_level_names = ["dagster", "dagster-pipes"]
    return [pkg.name for pkg in packages if pkg.name in top_level_names]


def get_top_level_modules() -> list[str]:
    """Get just the top-level Dagster module names (dagster and dagster_pipes).

    Returns:
        List of top-level module names: ["dagster", "dagster_pipes"]
    """
    packages = get_public_dagster_packages()
    top_level_names = ["dagster", "dagster-pipes"]
    return [pkg.module_name for pkg in packages if pkg.name in top_level_names]


def get_public_package_names() -> list[str]:
    """Get all public Dagster package names (top-level packages + libraries).

    Returns:
        List of all package names (e.g., ["dagster", "dagster-pipes", "dagster-aws", ...])
    """
    return [pkg.name for pkg in get_public_dagster_packages()]


def get_public_module_names() -> list[str]:
    """Get all public Dagster module names (top-level packages + libraries).

    Returns:
        List of all module names (e.g., ["dagster", "dagster_pipes", "dagster_aws", ...])
    """
    return [pkg.module_name for pkg in get_public_dagster_packages()]


def is_public_dagster_package(package_name: str) -> bool:
    """Check if a package name is a public Dagster package.

    Args:
        package_name: Package name to check (e.g., "dagster-aws")

    Returns:
        True if the package is a public Dagster package, False otherwise.
    """
    public_names = get_public_package_names()
    return package_name in public_names


def is_public_dagster_module(module_name: str) -> bool:
    """Check if a module name is a public Dagster module.

    Args:
        module_name: Module name to check (e.g., "dagster_aws")

    Returns:
        True if the module is a public Dagster module, False otherwise.
    """
    public_modules = get_public_module_names()
    return module_name in public_modules
