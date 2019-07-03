Expectations
============

Dagster has a first-class concept to capture data quality tests. We call these
data quality tests expectations.

Data pipelines have the property that they typically do not control
what data they ingest. Unlike a traditional application where you can
prevent users from entering malformed data, data pipelines do not have
that option. When unexpected data enters a pipeline and causes a software
error, typically the only recourse is to update your code.

Lying within the code of data pipelines are a whole host of implicit
assumptions about the nature of the data. One way to frame the goal of
expectations is to say that they make those implict assumption explicit.
And by making these a first class concept they can be described with metadata,
inspected, and configured to run in different ways.

You'll note the new concept of expecatations.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/expectations.py
   :linenos:
   :caption: expectations.py
   :emphasize-lines: 6

An :py:class:`ExpectationResult <dagster.ExpectationResult>` allows your solid to communicate the result
of performing a data quality test. This can include checks done on inputs before computing or checks done
before returning outputs if they were computed in an external system such as Spark.

If you run this pipeline, you'll notice some logging for the result of the expectation.

We'll use this config file.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/expectations_pass.yaml
   :linenos:
   :caption: expectations_pass.yaml

And then run:

.. code-block:: console

    $ dagster pipeline execute -f expectations.py \
    -n expectations_tutorial_pipeline -e \
    expectations_pass.yaml

In that execution you'll notice a passing expectation:

.. code-block:: console

    2019-07-03 10:38:48 - dagster - INFO -
            orig_message = "Solid add_ints passed expectation 'num_one_positive'"
        log_message_id = "b6a5fed4-643b-4053-9874-960d35b7fcb7"
        log_timestamp = "2019-07-03T17:38:48.397593"
                run_id = "1dddbca4-8473-4374-941e-b7ba852c121a"
                pipeline = "expectations_tutorial_pipeline"
    execution_epoch_time = 1562175528.392194
                step_key = "add_ints.compute"
                solid = "add_ints"
        solid_definition = "add_ints"
    2019-07-03 10:38:48 - dagster - INFO -
            orig_message = "Solid add_ints emitted output 'result' value 5"
        log_message_id = "634dc567-ed48-4d57-b623-14b980c5d36e"
        log_timestamp = "2019-07-03T17:38:48.398001"
                run_id = "1dddbca4-8473-4374-941e-b7ba852c121a"
                pipeline = "expectations_tutorial_pipeline"
    execution_epoch_time = 1562175528.392194
                step_key = "add_ints.compute"
                solid = "add_ints"
        solid_definition = "add_ints"

Now let's make this fail. So:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/expectations_fail.yaml
   :linenos:
   :caption: expectations_fail.yaml

And then:

.. code-block:: sh

    $ dagster pipeline execute -f expectations.py \
    -n expectations_tutorial_pipeline \
    -e expectations_fail.yaml

.. code-block:: console

    2019-07-03 10:45:22 - dagster - INFO -
            orig_message = "Solid add_ints failed expectation 'num_one_positive'"
        log_message_id = "64ab5299-4442-4fde-8bc5-b3ae102e4d12"
        log_timestamp = "2019-07-03T17:45:22.107882"
                run_id = "6f85e6cd-ebf3-4e55-b862-f64c3fedba7f"
                pipeline = "expectations_tutorial_pipeline"
    execution_epoch_time = 1562175922.099957
                step_key = "add_ints.compute"
                solid = "add_ints"
        solid_definition = "add_ints"
    2019-07-03 10:45:22 - dagster - INFO -
            orig_message = "Solid add_ints emitted output 'result' value 1"
        log_message_id = "a8d82e1c-b77a-41b9-a649-2bcd87d7a9ab"
        log_timestamp = "2019-07-03T17:45:22.108435"
                run_id = "6f85e6cd-ebf3-4e55-b862-f64c3fedba7f"
                pipeline = "expectations_tutorial_pipeline"
    execution_epoch_time = 1562175922.099957
                step_key = "add_ints.compute"
                solid = "add_ints"
        solid_definition = "add_ints"

Because the system is explictly aware of these expectations they are viewable in dagit.
The capabilities of this part of the system are currently quite immature, but we expect to develop
these more in the future.
