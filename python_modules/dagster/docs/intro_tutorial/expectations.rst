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

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/expectations.py
   :linenos:
   :caption: expectations.py
   :emphasize-lines: 17-24

At its core, an expectation is a function applied to either an input or an output.
Generally anywhere there is a type, you can apply an expectation. This function
can be as sophisticated as the user wants, anywhere from a simple null check to
checking thresholds of distrbutions or querying lookup tables.


If you run this pipeline, you'll notice some logging that indicates that the expectation
was processed

We'll use this config file.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/expectations_pass.yml
   :linenos:
   :caption: expectations_pass.yml

And then run:

.. code-block:: console

    $ dagster pipeline execute -f expectations.py \
    -n define_expectations_tutorial_pipeline -e \
    expectations_pass.yml

In that execution you'll notice a passing expectation:

.. code-block:: console

    2019-01-15 13:04:17 - dagster - INFO - orig_message="Execution of add_ints.output.num_one.expectation.check_positive succeeded in 0.06198883056640625" log_message_id="e903e121-e529-42ff-9561-b17dea553fba" run_id="71affcec-1c10-4a8b-9416-10115a01783f" pipeline="expectations_tutorial_pipeline" solid="add_ints" solid_definition="add_ints" event_type="EXECUTION_PLAN_STEP_SUCCESS" millis=0.06198883056640625 step_key="add_ints.output.num_one.expectation.check_positive"

Now let's make this fail. Currently the default behavior is to throw an error and halt execution
when an expectation fails. So:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/expectations_fail.yml
   :linenos:
   :caption: expectations_fail.yml

And then:

.. code-block:: sh

    $ dagster pipeline execute -f expectations.py \
    -n define_expectations_tutorial_pipeline \
    -e expectations_fail.yml

    dagster.core.errors.DagsterExpectationFailedError: 
    DagsterExpectationFailedError(solid=add_ints, 
    output=num_one, expectation=check_positive 
    value=-2)


Because the system is explictly aware of these expectations they are viewable in tools like dagit.
It can also configure the execution of these expectations. The capabilities of this aspect of the
system are currently quite immature, but we expect to develop these more in the future. The only
feature right now is the ability to skip expectations entirely. This is useful in a case where
expectations are expensive and you have a time-critical job you must. In that case you can
configure the pipeline to skip expectations entirely.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/expectations_skip_failed.yml
   :linenos:
   :caption: expectations_skip_fail.yml

.. code-block:: sh

    $ dagster pipeline execute -f expectations.py \
    -n define_expectations_tutorial_pipeline \
    -e expectations_skip_failed.yml

