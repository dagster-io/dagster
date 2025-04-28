from dagster._core.definitions.selector import RepositorySelector

from dagster_graphql.schema.components import (
    GrapheneCodeLocationComponentsManifest,
    GrapheneComponentFileDiffInformation,
    GrapheneComponentInstance,
    GrapheneComponentInstanceFile,
    GrapheneComponentType,
)


def fetch_code_location_components_manifest(
    graphene_info, repository_selector: RepositorySelector
) -> GrapheneCodeLocationComponentsManifest:
    return GrapheneCodeLocationComponentsManifest(
        componentInstances=[
            GrapheneComponentInstance(
                path=["my_sling_sync"],
                files=[
                    GrapheneComponentInstanceFile(
                        path=["component.yaml"],
                        diffInformation=GrapheneComponentFileDiffInformation(added=0, removed=0),
                        contents="""
type: dagster_sling.SlingReplicationCollectionComponent

attributes:
  replications:
    - path: replication.yaml
                        """,
                    ),
                    GrapheneComponentInstanceFile(
                        path=["replication.yaml"],
                        diffInformation=GrapheneComponentFileDiffInformation(added=0, removed=0),
                        contents="""
source: LOCAL
target: DUCKDB

defaults:
  mode: full-refresh
  object: "{stream_table}"

streams:
  file://raw_customers.csv:
    object: "main.raw_customers"
  file://raw_orders.csv:
    object: "main.raw_orders"
  file://raw_payments.csv:
    object: "main.raw_payments"
                        """,
                    ),
                ],
            )
        ],
        componentTypes=[
            GrapheneComponentType(
                key="dagster.DefinitionsComponent",
                schema=None,
            ),
            GrapheneComponentType(
                key="dagster_sling.SlingReplicationCollectionComponent",
                schema=None,
            ),
        ],
    )
