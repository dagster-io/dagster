.. _scheduler:

Scheduling pipeline runs
------------------------

Dagster includes a simple built-in scheduler that works with Dagit for control and monitoring.
Suppose that we need to run our simple cereal pipeline every morning before breakfast, at 6:45 AM.

Requirements
^^^^^^^^^^^^
You'll need to install the ``dagster-cron`` library.

.. code-block:: shell

    $ pip install dagster-cron

You must also ensure that ``cron`` is installed on the machine you're running the scheduler on.

Pipeline
^^^^^^^^

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/scheduler.py
   :linenos:
   :lines: 1-34
   :caption: scheduler.py

As before, we've defined some solids, a pipeline, and a repository.

Defining the scheduler
^^^^^^^^^^^^^^^^^^^^^^

We first need to define the Scheduler on our :py:class:`~dagster.core.instance.DagsterInstance`. For
now, the only implemented scheduler is ``dagster_cron.SystemCronScheduler``, but this is pluggable
(and you can write your own). To use the scheduler, add the following lines
to your ``$DAGSTER_HOME/dagster.yaml``:


.. code-block:: yaml
   :caption: dagster.yaml

    scheduler:
        module: dagster_cron.cron_scheduler
        class: SystemCronScheduler
        config:
            artifacts_dir: /path/to/dagster_home/schedule


Defining schedules
^^^^^^^^^^^^^^^^^^

Now we'll write a :py:class:`ScheduleDefinition <dagster.ScheduleDefinition>` to define the schedule
we want. We pass the ``cron_schedule`` parameter to this class to define when the pipeline should run
using the standard cron syntax; the other parameters determine other familiar aspects of how the
pipeline will run, such as its config.

We wrap the schedule definition in a function decorated with
:py:class:`@schedules <dagster.schedules>`:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/scheduler.py
   :linenos:
   :lines: 36-45
   :lineno-start: 38
   :caption: scheduler.py

To complete the picture, we'll need to extend the ``repository.yaml`` structure we've met before
with a new key, ``scheduler``.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/scheduler.yaml
   :linenos:
   :caption: scheduler.yaml


Starting schedules
^^^^^^^^^^^^^^^^^^

Whenever we make changes to schedule definitions using the ``SystemCronScheduler``, we need to run
``dagster schedule up``. This utility will create, update, or remove schedules in the underlying
system cron file as appropriate to assure it is consistent with the schedule definitions in code.

To preview the changes, first run:

.. code-block:: console

    $ dagster schedule up --preview -y scheduler.yaml
    Planned Changes:
      + good_morning (add)

After confirming schedule changes are as expected, run:

.. code-block:: console

    $ dagster schedule up -y scheduler.yaml
    Changes:
      + good_morning (add)

Verify that the ``good_morning`` scheduled job has been added to ``cron``:

.. code-block:: console

    $ crontab -l

If the ``good_morning`` job is not listed, you may have to start it with:

.. code-block:: console

    $ dagster schedule start good_morning

Now, we can load dagit to view the schedule and monitor runs:

.. code-block:: console

    $ dagit -y scheduler.yaml


Cron filters
^^^^^^^^^^^^^^^^^^

If you need to define a more specific schedule than cron allows, you can pass a function in the
``should_execute`` argument to :py:class:`ScheduleDefinition <dagster.ScheduleDefinition>`.

For example, we can define a filter that only returns `True` on weekdays:


.. code-block:: python

    import datetime

    def weekday_filter():
        weekno = datetime.datetime.today().weekday()
        # Returns true if current day is a weekday
        return weekno < 5

If we combine this `should_execute` filter with a `cron_schedule` that runs at 6:45am every day,
then we’ll have a schedule that runs at 6:45am only on weekdays.

.. code-block:: python

    good_weekday_morning = ScheduleDefinition(
        name="good_weekday_morning",
        cron_schedule="45 6 * * *",
        pipeline_name="hello_cereal_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
        should_execute=weekday_filter,
    )
