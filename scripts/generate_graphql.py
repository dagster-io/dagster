"""Generate GraphQL code for dagster-oss."""

import json
import shutil
import subprocess
from pathlib import Path

from dagster._core.workspace.permissions import Permissions
from dagster_graphql.schema import create_schema
from graphql import (
    GraphQLInterfaceType,
    GraphQLSchema,
    GraphQLUnionType,
    build_client_schema,
    introspection_from_schema,
    print_schema,
)

REPO_ROOT = Path(__file__).resolve().parent.parent  # dagster-oss/
UI_CORE = REPO_ROOT / "js_modules" / "ui-core"
UI_CORE_GRAPHQL_DIR = UI_CORE / "src" / "graphql"
REST_RESOURCES = REPO_ROOT / "python_modules" / "libraries" / "dagster-rest-resources"

INTERNAL_ROOT = REPO_ROOT.parent  # internal/
APP_CLOUD = INTERNAL_ROOT / "dagster-cloud" / "js_modules" / "app-cloud"
APP_CLOUD_GRAPHQL_DIR = APP_CLOUD / "src" / "graphql"


def schema_to_sdl(graphql_schema: GraphQLSchema) -> str:
    """Convert a GraphQLSchema to SDL without descriptions."""
    introspection = introspection_from_schema(graphql_schema, descriptions=False)
    rebuilt = build_client_schema(introspection)
    return print_schema(rebuilt)


def write_and_prettify(path: Path, content: str, *, cwd: Path):
    path.write_text(content, "utf-8")
    subprocess.run(
        ["yarn", "prettier", "--log-level", "silent", "--write", str(path)],
        check=True,
        cwd=cwd,
    )


def generate_oss_schema(gql_schema: GraphQLSchema):
    print("Generating OSS schema...")
    oss_sdl = schema_to_sdl(gql_schema)
    write_and_prettify(
        UI_CORE_GRAPHQL_DIR / "schema.graphql",
        content=oss_sdl,
        cwd=UI_CORE,
    )
    print("OSS schema complete")


def generate_oss_possible_types(gql_schema: GraphQLSchema):
    print("Generating OSS possibleTypes...")
    possible_types = {
        type_name: [t.name for t in gql_schema.get_possible_types(type_obj)]
        for type_name, type_obj in gql_schema.type_map.items()
        if isinstance(type_obj, (GraphQLInterfaceType, GraphQLUnionType))
    }
    write_and_prettify(
        UI_CORE_GRAPHQL_DIR / "possibleTypes.generated.json",
        content=json.dumps(possible_types),
        cwd=UI_CORE,
    )
    print("OSS possibleTypes complete")


def generate_oss_types():
    """Run graphql-codegen and post-process version hashes."""
    print("Generating OSS types...")
    # Clean old generated types
    for types_dir in sorted(UI_CORE.glob("src/**/types")):
        if types_dir.is_dir():
            shutil.rmtree(types_dir)

    # Run graphql-codegen
    subprocess.run(["yarn", "graphql-codegen"], check=True, cwd=UI_CORE)

    # Post-process: append version hash constants to .types.ts files
    client_json_path = UI_CORE / "client.json"
    client_json_contents = client_json_path.read_text(encoding="utf-8")
    client_json_items = json.loads(client_json_contents).items()
    for types_file in sorted(UI_CORE.rglob("*.types.ts")):
        modified = False
        content = types_file.read_text(encoding="utf-8")
        for operation_name, hash_val in client_json_items:
            if f"export type {operation_name}" in content:
                version_const = f"\nexport const {operation_name}Version = '{hash_val}';\n"
                if f"{operation_name}Version" not in content:
                    content += version_const
                    modified = True
        if modified:
            types_file.write_text(content, encoding="utf-8")
    print("OSS types complete")


def generate_oss_permissions():
    print("Generating OSS permissions...")
    permissions = [{"permission": p.value} for p in Permissions]
    write_and_prettify(
        UI_CORE_GRAPHQL_DIR / "permissions.json",
        content=json.dumps(permissions),
        cwd=UI_CORE,
    )
    print("OSS permissions complete")


def _are_dagster_cloud_packages_available():
    """Check if dagster_cloud_dagit is available (not in OSS repo or CI OSS-only environments)."""
    try:
        import dagster_cloud_dagit  # noqa: F401  # ty: ignore[unresolved-import]

        return True
    except ImportError:
        return False


def generate_app_cloud_schema(gql_schema: GraphQLSchema):
    print("Generating App Cloud schema (for dagster-rest-resources)...")
    cloud_sdl = schema_to_sdl(gql_schema)
    write_and_prettify(
        APP_CLOUD_GRAPHQL_DIR / "schema.graphql",
        content=cloud_sdl,
        cwd=APP_CLOUD,
    )
    print("App Cloud schema complete")


def generate_dagster_rest_resources_artifacts():
    print("Generating dagster-rest-resources artifacts...")
    subprocess.run(
        ["uv", "run", "--active", "--no-project", "ariadne-codegen"],
        check=True,
        cwd=REST_RESOURCES,
    )
    print("dagster-rest-resources artifacts complete")


def main():
    print("================Generating OSS Graphql...================")
    oss_gql_schema = create_schema().graphql_schema

    generate_oss_schema(oss_gql_schema)
    generate_oss_possible_types(oss_gql_schema)
    generate_oss_types()
    generate_oss_permissions()

    if _are_dagster_cloud_packages_available():
        from dagster_cloud_dagit.graphql.schema import (  # ty: ignore[unresolved-import]
            create_dagster_cloud_dagit_schema,
        )

        app_cloud_gql_schema = create_dagster_cloud_dagit_schema().graphql_schema

        generate_app_cloud_schema(app_cloud_gql_schema)
        generate_dagster_rest_resources_artifacts()
    else:
        print("Skipping dagster-rest-resources codegen (dagster_cloud_dagit not installed).")

    print("================OSS Graphql Complete================")


if __name__ == "__main__":
    main()
