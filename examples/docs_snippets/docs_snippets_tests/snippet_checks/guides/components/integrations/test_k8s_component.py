import textwrap
from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.utils import DAGSTER_ROOT
from docs_snippets_tests.snippet_checks.utils import (
    isolated_snippet_generation_environment,
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "integrations"
    / "k8s-component"
)


def test_components_docs_k8s(
    update_snippets: bool,
    update_screenshots: bool,
    get_selenium_driver,
) -> None:
    with (
        isolated_snippet_generation_environment(
            should_update_snippets=update_snippets,
            snapshot_base_dir=SNIPPETS_DIR,
            global_snippet_replace_regexes=[
                MASK_VENV,
                MASK_USING_LOG_MESSAGE,
                MASK_MY_PROJECT,
            ],
        ) as context,
        ExitStack() as stack,
    ):
        # 1-scaffold-project.txt: Project creation
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # 2-install-dagster-k8s.txt: Install dagster-k8s package
        context.run_command_and_snippet_output(
            cmd="uv add dagster-k8s",
            snippet_path=f"{context.get_next_snip_number()}-install-dagster-k8s.txt",
        )

        # 3-scaffold-k8s-component.txt: Component scaffolding (manual command for now)
        context.create_file(
            Path("dummy_scaffold.txt"),
            contents="dg scaffold defs dagster_k8s.PipesK8sComponent process_data",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-k8s-component.txt",
        )

        # 3-tree.txt: Project structure (static for now since component isn't registered)
        context.create_file(
            Path("dummy_tree.txt"),
            contents=textwrap.dedent(
                """\
                tree my_project/defs

                my_project/defs
                ├── __init__.py
                └── process_data
                    └── defs.yaml

                2 directories, 2 files
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
        )

        # 4-dockerfile: Docker image definition
        context.create_file(
            Path("dummy_dockerfile"),
            contents=textwrap.dedent(
                """\
                FROM python:3.11-slim

                # Install required packages
                RUN pip install pandas dagster-pipes

                # Copy the processing script
                COPY process_data.py /app/process_data.py

                WORKDIR /app

                # Set the default command
                CMD ["python", "process_data.py"]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-dockerfile",
        )

        # 5-process-data-script.py: Simple data processing script
        context.create_file(
            Path("dummy_process_data.py"),
            contents=textwrap.dedent(
                """\
                import pandas as pd

                # Sample transaction data (in a real scenario, this might come from a database or API)
                transaction_data = {
                    "transaction_id": ["T001", "T002", "T003", "T004"],
                    "customer_id": ["C123", "C456", "C789", "C123"],
                    "product": ["Widget A", "Widget B", "Widget A", "Widget C"],
                    "quantity": [2, 1, 3, 1],
                    "price": [19.99, 39.99, 19.99, 29.99],
                }

                df = pd.DataFrame(transaction_data)
                df["total_amount"] = df["quantity"] * df["price"]

                # Calculate metrics
                total_revenue = df["total_amount"].sum()
                unique_customers = df["customer_id"].nunique()
                avg_order_value = df["total_amount"].mean()

                print(f"Data processing completed successfully")  # noqa: T201
                print(f"Total revenue: ${total_revenue}")  # noqa: T201
                print(f"Unique customers: {unique_customers}")  # noqa: T201
                print(f"Average order value: ${avg_order_value:.2f}")  # noqa: T201
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-process-data-script.py",
        )

        # 6-build-image.txt: Docker build commands
        context.create_file(
            Path("dummy_build.txt"),
            contents=textwrap.dedent(
                """\
                docker build -t my-data-processor:latest .
                docker tag my-data-processor:latest my-registry/my-data-processor:latest
                docker push my-registry/my-data-processor:latest
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-build-image.txt",
        )

        # 7-customized-component.yaml: Basic component configuration
        # Create the actual component file in the right place for dg to find it
        context.create_file(
            Path("my_project") / "defs" / "process_data" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_k8s.PipesK8sComponent

                name: process_data
                assets:
                  - key: processed_transaction_data
                    description: "Processed transaction data with calculated metrics"
                    group_name: "analytics"
                    kinds: ["python", "kubernetes"]

                image: my-registry/my-data-processor:latest
                command: ["python", "process_data.py"]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # 8-list-defs.txt: List definitions output (static since component not yet in public API)
        context.create_file(
            Path("dummy_list_defs.txt"),
            contents=textwrap.dedent(
                """\
                dg list defs

                ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                ┃ Section ┃ Definitions                                                                                                ┃
                ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
                │ Assets  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
                │         │ ┃ Key                          ┃ Group     ┃ Deps ┃ Kinds          ┃ Description                                         ┃ │
                │         │ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
                │         │ │ processed_transaction_data   │ analytics │      │ python         │ Processed transaction data with calculated          │ │
                │         │ │                              │           │      │ kubernetes     │ metrics                                             │ │
                │         │ └──────────────────────────────┴───────────┴──────┴────────────────┴─────────────────────────────────────────────────────┘ │
                └─────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # 9-launch.txt: Launch command
        context.create_file(
            Path("dummy_launch.txt"),
            contents="dg dev",
            snippet_path=f"{context.get_next_snip_number()}-launch.txt",
        )

        # 10-advanced-pipes-script.py: Advanced script with Dagster Pipes
        context.create_file(
            Path("dummy_advanced_script.py"),
            contents=textwrap.dedent(
                """\
                import pandas as pd
                from dagster_pipes import open_dagster_pipes

                # Sample transaction data (in a real scenario, this might come from a database or API)
                transaction_data = {
                    "transaction_id": ["T001", "T002", "T003", "T004"],
                    "customer_id": ["C123", "C456", "C789", "C123"],
                    "product": ["Widget A", "Widget B", "Widget A", "Widget C"],
                    "quantity": [2, 1, 3, 1],
                    "price": [19.99, 39.99, 19.99, 29.99],
                }

                with open_dagster_pipes() as context:
                    df = pd.DataFrame(transaction_data)
                    df["total_amount"] = df["quantity"] * df["price"]
                    
                    # Calculate metrics
                    total_revenue = df["total_amount"].sum()
                    unique_customers = df["customer_id"].nunique()
                    avg_order_value = df["total_amount"].mean()
                    
                    # Log the results to Dagster
                    context.log.info(f"Data processing completed successfully")
                    context.log.info(f"Processed {len(df)} transactions")
                    
                    # Report asset materialization with rich metadata
                    context.report_asset_materialization(
                        metadata={
                            "total_revenue": total_revenue,
                            "unique_customers": unique_customers,
                            "avg_order_value": avg_order_value,
                            "num_transactions": len(df),
                            "top_product": df.groupby("product")["total_amount"].sum().idxmax(),
                        }
                    )
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-advanced-pipes-script.py",
        )

        # 11-multiple-jobs-component.yaml: Multiple jobs configuration
        context.create_file(
            Path("dummy_multiple_jobs.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster_k8s.PipesK8sComponent

                name: transaction_processor
                assets:
                  - key: processed_transaction_data
                    description: "Processed transaction data"
                    group_name: "analytics"

                image: my-registry/transaction-processor:latest
                command: ["python", "process_transactions.py"]
                ---
                type: dagster_k8s.PipesK8sComponent

                name: customer_analyzer
                assets:
                  - key: customer_insights
                    description: "Customer behavior insights"
                    group_name: "analytics"

                image: my-registry/customer-analyzer:latest
                command: ["python", "analyze_customers.py"]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-multiple-jobs-component.yaml",
        )

        # 12-dependencies-component.yaml: Dependencies example
        context.create_file(
            Path("dummy_dependencies.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster_k8s.PipesK8sComponent

                name: transaction_processor
                assets:
                  - key: processed_transaction_data
                    description: "Processed transaction data"
                    group_name: "analytics"

                image: my-registry/transaction-processor:latest
                command: ["python", "process_transactions.py"]
                ---
                type: dagster_k8s.PipesK8sComponent

                name: customer_analyzer
                assets:
                  - key: customer_insights
                    description: "Customer behavior insights"
                    group_name: "analytics"
                    deps: [processed_transaction_data]

                image: my-registry/customer-analyzer:latest
                command: ["python", "analyze_customers.py"]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-dependencies-component.yaml",
        )

        # 13-automation-component.yaml: Automation conditions
        context.create_file(
            Path("dummy_automation.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster_k8s.PipesK8sComponent

                name: process_data
                assets:
                  - key: processed_transaction_data
                    description: "Processed transaction data with calculated metrics"
                    group_name: "analytics"
                    automation_condition: "{{ automation_condition.on_cron('@daily') }}"

                image: my-registry/my-data-processor:latest
                command: ["python", "process_data.py"]
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-automation-component.yaml",
        )

        # 14-resource-config-component.yaml: Resource configuration
        context.create_file(
            Path("dummy_resources.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster_k8s.PipesK8sComponent

                name: process_data
                assets:
                  - key: processed_transaction_data
                    description: "Processed transaction data"
                    group_name: "analytics"

                image: my-registry/my-data-processor:latest
                command: ["python", "process_data.py"]
                env:
                  DATABASE_URL: "postgresql://user:pass@db:5432/mydb"
                  LOG_LEVEL: "INFO"
                base_pod_spec:
                  containers:
                    - name: main
                      resources:
                        requests:
                          memory: "512Mi"
                          cpu: "250m"
                        limits:
                          memory: "1Gi"
                          cpu: "500m"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-resource-config-component.yaml",
        )

        # 15-advanced-k8s-component.yaml: Advanced Kubernetes configuration
        context.create_file(
            Path("dummy_advanced_k8s.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster_k8s.PipesK8sComponent

                name: advanced_data_processor
                assets:
                  - key: processed_data
                    description: "Advanced data processing with custom K8s config"
                    group_name: "analytics"

                image: my-registry/advanced-processor:latest
                command: ["python", "advanced_process.py"]
                namespace: data-processing
                env:
                  WORKER_THREADS: "4"
                  BATCH_SIZE: "1000"
                base_pod_meta:
                  labels:
                    app: dagster-data-processor
                    version: v1.0
                  annotations:
                    monitoring.io/scrape: "true"
                base_pod_spec:
                  serviceAccountName: data-processor-sa
                  containers:
                    - name: main
                      resources:
                        requests:
                          memory: "2Gi"
                          cpu: "1"
                        limits:
                          memory: "4Gi"
                          cpu: "2"
                      volumeMounts:
                        - name: data-volume
                          mountPath: /data
                  volumes:
                    - name: data-volume
                      persistentVolumeClaim:
                        claimName: data-pvc
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-advanced-k8s-component.yaml",
        )
