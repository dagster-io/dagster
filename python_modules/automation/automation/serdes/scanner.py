import importlib
from pathlib import Path

import click


def discover_and_import_serdes_modules(package_name: str, verbose: bool):
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        raise ImportError(f"Could not import package '{package_name}': {e}") from e

    # Get package path
    if hasattr(package, "__path__"):
        package_paths = list(package.__path__)
    else:
        package_paths = [str(Path(package.__file__).parent)]

    serdes_modules = []

    # Search for files containing @whitelist_for_serdes
    for package_path in package_paths:
        package_path_obj = Path(package_path)
        if verbose:
            click.echo(f"Searching in: {package_path}", err=True)

        for py_file in package_path_obj.rglob("*.py"):
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                if "@whitelist_for_serdes" in content or "whitelist_for_serdes(" in content:
                    relative_path = py_file.relative_to(package_path_obj)
                    module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

                    if module_parts[-1] == "__init__":
                        module_parts = module_parts[:-1]

                    if module_parts:
                        module_name = f"{package_name}.{'.'.join(module_parts)}"
                    else:
                        module_name = package_name

                    serdes_modules.append(module_name)
            except Exception as e:
                if verbose:
                    click.echo(f"Warning: Could not read {py_file}: {e}", err=True)
                continue

    # Import all discovered modules
    if verbose:
        click.echo(f"\nFound {len(serdes_modules)} modules with serdes types", err=True)

    imported_count = 0
    failed_imports = []

    for module_name in sorted(serdes_modules):
        try:
            if verbose:
                click.echo(f"Importing: {module_name}", err=True)
            importlib.import_module(module_name)
            imported_count += 1
        except Exception as e:
            failed_imports.append((module_name, str(e)))
            if verbose:
                click.echo(f"Warning: Failed to import {module_name}: {e}", err=True)

    if verbose:
        click.echo(
            f"\nSuccessfully imported {imported_count}/{len(serdes_modules)} modules", err=True
        )
        if failed_imports:
            click.echo(f"Failed imports: {len(failed_imports)}", err=True)

    return imported_count, failed_imports
