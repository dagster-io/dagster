import json
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Optional, TypeAlias

import click
import dagster_shared.check as check
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import snakecase
from dagster_shared.scaffold import scaffold_subtree
from dagster_shared.serdes.objects.package_entry import EnvRegistryKey
from dagster_shared.seven import match_module_pattern

ScaffoldFormatOptions: TypeAlias = Literal["yaml", "python"]


def scaffold_component(
    *, dg_context: DgContext, class_name: str, module_name: str, model: bool
) -> None:
    module_parts = module_name.split(".")
    module_path = dg_context.root_path
    for i in range(len(dg_context.root_module_name.split(".")), len(module_parts) - 1):
        module = ".".join(module_parts[: i + 1])
        module_path = dg_context.get_path_for_local_module(module, require_exists=False)
        if not module_path.exists():
            click.echo(f"Creating module at: {module_path}")
            module_path.mkdir()
        (module_path / "__init__.py").touch()

    scaffold_subtree(
        path=module_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        project_template_path=Path(__file__).parent / "templates" / "COMPONENT_TYPE",
        project_name=module_parts[-1],
        name=class_name,
        model=model,
    )

    # backcompat -- dagster_dg_cli.plugin entry point
    if dg_context.has_registry_module_entry_point:
        with open(module_path / "__init__.py") as f:
            lines = f.readlines()
        lines.append(f"from {module_name} import {class_name} as {class_name}\n")
        with open(module_path / "__init__.py", "w") as f:
            f.writelines(lines)

    # no plugin entry point, add to project plugin modules
    else:
        project_config = check.not_none(dg_context.config.project)
        if not any(
            match_module_pattern(module_name, pattern)
            for pattern in project_config.registry_modules
        ):
            dg_context.add_project_registry_module(module_name)
    click.echo(f"Scaffolded Dagster component at {module_path}/{module_parts[-1]}.py.")


# ########################
# ##### INLINE COMPONENT
# ########################


def scaffold_inline_component(
    path: Path,
    typename: str,
    superclass: Optional[str],
    dg_context: "DgContext",
) -> None:
    full_path = dg_context.defs_path / path
    full_path.mkdir(parents=True, exist_ok=True)
    click.echo(
        f"Creating a Dagster inline component and corresponding component instance at {path}."
    )

    component_path = full_path / f"{snakecase(typename)}.py"
    if superclass:
        key = EnvRegistryKey.from_typename(superclass)
        superclass_import_lines = [
            f"from {key.namespace} import {key.name}",
        ]
        superclass_list = key.name
    else:
        superclass_import_lines = []
        superclass_list = "dg.Component, dg.Model, dg.Resolvable"

    component_lines = [
        "import dagster as dg",
        *superclass_import_lines,
        "",
        f"class {typename}({superclass_list}):",
        "    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:",
        "        return dg.Definitions()",
    ]
    component_path.write_text("\n".join(component_lines))

    containing_module = ".".join(
        [
            dg_context.defs_module_name,
            str(path).replace("/", "."),
            f"{snakecase(typename)}",
        ]
    )
    defs_path = full_path / "defs.yaml"
    defs_path.write_text(
        textwrap.dedent(f"""
        type: {containing_module}.{typename}
        attributes: {{}}
    """).strip()
    )


# ####################
# ##### REGISTRY OBJECT
# ####################


def scaffold_registry_object(
    path: Path,
    typename: str,
    scaffold_params: Optional[Mapping[str, Any]],
    dg_context: "DgContext",
    scaffold_format: ScaffoldFormatOptions,
    append: bool = False,
) -> None:
    from dagster.components.component_scaffolding import scaffold_object

    scaffold_object(
        path,
        typename,
        json.dumps(scaffold_params) if scaffold_params else None,
        scaffold_format,
        dg_context.root_path,
        append,
    )
