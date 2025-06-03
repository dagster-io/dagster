import json
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Optional

import click
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import snakecase, validate_dagster_availability
from dagster_shared.scaffold import scaffold_subtree
from dagster_shared.serdes.objects.package_entry import PluginObjectKey
from typing_extensions import TypeAlias

ScaffoldFormatOptions: TypeAlias = Literal["yaml", "python"]


def scaffold_component(
    *, dg_context: DgContext, class_name: str, module_name: str, model: bool
) -> None:
    root_path = Path(dg_context.default_plugin_module_path)
    click.echo(f"Creating a Dagster component type at {root_path}/{module_name}.py.")

    scaffold_subtree(
        path=root_path,
        name_placeholder="COMPONENT_TYPE_NAME_PLACEHOLDER",
        project_template_path=Path(__file__).parent / "templates" / "COMPONENT_TYPE",
        project_name=module_name,
        name=class_name,
        model=model,
    )

    with open(root_path / "__init__.py") as f:
        lines = f.readlines()
    lines.append(
        f"from {dg_context.default_plugin_module_name}.{module_name} import {class_name} as {class_name}\n"
    )
    with open(root_path / "__init__.py", "w") as f:
        f.writelines(lines)

    click.echo(f"Scaffolded files for Dagster component type at {root_path}/{module_name}.py.")


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
        key = PluginObjectKey.from_typename(superclass)
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
# ##### LIBRARY OBJECT
# ####################


def scaffold_library_object(
    path: Path,
    typename: str,
    scaffold_params: Optional[Mapping[str, Any]],
    dg_context: "DgContext",
    scaffold_format: ScaffoldFormatOptions,
) -> None:
    validate_dagster_availability()
    from dagster.components.cli.scaffold import scaffold_object_command_impl

    scaffold_object_command_impl(
        typename,
        path,
        json.dumps(scaffold_params) if scaffold_params else None,
        scaffold_format,
        dg_context.root_path,
    )
