from pathlib import Path

import yaml

target_dir = Path(__file__).parent.parent / "airflow_dags" / "proxied_state"
# Ensure the target directory exists
target_dir.mkdir(parents=True, exist_ok=True)


def scaffold_proxied_state(num_dags: int, num_tasks: int, proxied_state: bool):
    # Ensure the target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    for i in range(num_dags):
        yaml_dict = {
            "tasks": [{"id": f"task_{i}_{j}", "proxied": proxied_state} for j in range(num_tasks)],
        }
        # Write to a file dag_{i}.yaml
        with open(target_dir / f"dag_{i}.yaml", "w") as f:
            yaml.dump(yaml_dict, f)
