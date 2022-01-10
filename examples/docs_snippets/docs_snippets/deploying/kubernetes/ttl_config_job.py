from dagster import job, op

@op
def my_op():
    print("foo")

@job(
  tags = {
    'dagster-k8s/config': {
      'job_spec_config': {
        'ttl_seconds_after_finished': 7200
      }
    }
  }
)
def my_job():
  my_op()
