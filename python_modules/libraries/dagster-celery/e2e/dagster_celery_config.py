import os

# Override the broker URL to use credentials from environment variables.
# dagster_celery.make_app imports this module when present to override defaults.
_rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
_rabbitmq_host = os.getenv("DAGSTER_CELERY_BROKER_HOST", "localhost")

broker_url = f"pyamqp://test:{_rabbitmq_password}@{_rabbitmq_host}:5672//"

result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://dagster-redis-master:6379/0")
