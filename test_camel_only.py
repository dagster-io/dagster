import sys
from dagster import job, op
from dagster._core.errors import DagsterInvalidConfigError

@op
def my_op():
    return "hello, world"

# Job with camelCase configuration, which is expected to be invalid in a Kubernetes context.
@job(tags={
    "dagster-k8s/config": {
        "containerConfig": {  # camelCase key (should be snake_case)
            "resources": {
                "requests": {"cpu": "500m", "memory": "512Mi"},
                "limits": {"cpu": "1000m", "memory": "1024Mi"},
            }
        },
        "podSpecConfig": {  # camelCase key (should be snake_case)
            "nodeSelector": {"kubernetes.io/hostname": "special-node"},
            "tolerations": [{"key": "special", "operator": "Exists"}]
        }
    }
})
def my_k8s_job_camel():
    my_op()

if __name__ == "__main__":
    print("Testing job with camelCase configuration...")
    try:
        # Attempt to execute the job in-process.
        # Note: In-process execution may not trigger the Kubernetes config validation error.
        result = my_k8s_job_camel.execute_in_process()
        print("Job executed. (In-process execution did not trigger the error):")
        print(result)
    except DagsterInvalidConfigError as e:
        print("Caught DagsterInvalidConfigError as expected:")
        print(e)
    except Exception as e:
        print("Caught an unexpected exception:")
        print(e)
