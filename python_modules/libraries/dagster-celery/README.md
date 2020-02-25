## dagster-celery

### Quickstart

To get a local rabbitmq broker started and available via the default `pyamqp://guest@localhost:5672`, in this directory run:

    docker-compose up

To run a celery worker:

    celery -A dagster_celery.tasks worker -l info

To start multiple workers in the background, run:

    celery multi start w2 -A dagster_celery.tasks -l info

To execute a pipeline using the celery-backed executor, you'll need to add the celery executor to
a mode definition on the pipeline:

    from dagster import default_executors
    from dagster_celery import celery_executor

    @pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [celery_executor])])
    def my_pipeline():
        pass

Then you can use config like the following to execute the pipeline:

    execution:
      celery:

#### Monitoring your Celery tasks.

We advise using [Flower](https://celery.readthedocs.io/en/latest/userguide/monitoring.html#flower-real-time-celery-web-monitor):

    celery -A dagster_celery.tasks flower

#### Customizing the Celery broker, backend, and other app configuration

By default this will use `amqp://guest:**@localhost:5672//` as the Celery broker URL and `rpc://`
as the results backend. In production, you will want to change these values. Pending the
introduction of a dagster_celery CLI, that would entail writing a Python module `my_module` as
follows:

    from celery import Celery

    from dagster_celery.tasks import create_task

    app = Celery('dagster', broker_url='some://custom@value', ...)

    execute_query = create_task(app)

    if __name__ == '__main__':
        app.worker_main()

You can then run the celery worker using:

    celery -A my_module worker --loglevel=info

#### Celery best practices

Celery is a rich and full-featured system. We've found the following resources helpful:

- Deni Bertović's [Celery best practices](https://denibertovic.com/posts/celery-best-practices/)
- Pawel Zadrozny's [series of articles](https://pawelzny.com/python/celery/2017/08/14/celery-4-tasks-best-practices/) on Celery best practices
- Balthazar Rouberol's [Celery best practices](https://blog.balthazar-rouberol.com/celery-best-practices)
