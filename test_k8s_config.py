import sys
from dagster import job, op

@op
def my_op():
    return "hello, world"

# Job with camelCase configuration (expected to raise an error)
@job(tags={
    "dagster-k8s/config": {
        "containerConfig": {  # Using camelCase – should fail.
            "resources": {
                "requests": {"cpu": "500m", "memory": "512Mi"},
                "limits": {"cpu": "1000m", "memory": "1024Mi"},
            }
        },
        "podSpecConfig": {  # Using camelCase – should fail.
            "nodeSelector": {"kubernetes.io/hostname": "special-node"},
            "tolerations": [{"key": "special", "operator": "Exists"}]
        }
    }
})
def my_k8s_job_camel():
    my_op()

# Job with snake_case configuration (expected to work correctly)
@job(tags={
    "dagster-k8s/config": {
        "container_config": {  # Using snake_case – correct.
            "resources": {
                "requests": {"cpu": "500m", "memory": "512Mi"},
                "limits": {"cpu": "1000m", "memory": "1024Mi"},
            }
        },
        "pod_spec_config": {  # Using snake_case – correct.
            "nodeSelector": {"kubernetes.io/hostname": "special-node"},
            "tolerations": [{"key": "special", "operator": "Exists"}]
        }
    }
})
def my_k8s_job_snake():
    my_op()

if __name__ == "__main__":
    # Usage: python test_k8s_config.py [camel|snake]
    if len(sys.argv) < 2:
        print("Usage: python test_k8s_config.py [camel|snake]")
        sys.exit(1)
    
    job_type = sys.argv[1].lower()
    
    if job_type == "camel":
        print("Executing job with camelCase configuration (expected to fail)...")
        # This should trigger a DagsterInvalidConfigError.
        result = my_k8s_job_camel.execute_in_process()
        print(result)
    elif job_type == "snake":
        print("Executing job with snake_case configuration (expected to succeed)...")
        result = my_k8s_job_snake.execute_in_process()
        print(result)
    else:
        print("Unknown argument. Use 'camel' or 'snake'.")
        sys.exit(1)
