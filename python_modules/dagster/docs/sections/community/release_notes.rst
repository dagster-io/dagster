Release Notes
=============

Dagster versions follow the guidelines in `PEP 440 <https://www.python.org/dev/peps/pep-0440//>`_.

To make dependency management easier in the context of a monorepo with many installable projects,
package versions move in lockstep with each other and with git tags. 

As the API is still in flux, we aren't following strict semantic versioning rules at this point, but roughly
intend micro versions to reflect a regular release schedule and minor versions to reflect
milestones in the framework's capability.

0.4.1
-----
**Compatibility**
- Dagster-airflow now works with Python 3.7 (since Airflow 1.10.3 now supports Python 3.7).

0.4.0
-----
**API Changes**

- There is now a new top-level configuration section ``storage`` which controls whether or not
  execution should store intermediate values and the history of pipeline runs on the filesystem,
  on S3, or in memory. The ``dagster`` CLI now includes options to list and wipe pipeline run
  history. Facilities are provided for user-defined types to override the default serialization
  used for storage.
- Similarily, there is a new configuration for ``RunConfig`` where the user can specify
  intermediate value storage via an API.
- ``OutputDefinition`` now contains an explicit ``is_optional`` parameter and defaults to being
  not optional.
- New functionality in ``dagster.check``: ``is_list``
- New functionality in ``dagster.seven``: py23-compatible ``FileNotFoundError``, ``json.dump``,
  ``json.dumps``.
- Dagster default logging is now multiline for readability.
- The ``Nothing`` type now allows dependencies to be constructed between solids that do not have
  data dependencies.
- Many error messages have been improved.
- ``throw_on_user_error`` has been renamed to ``raise_on_error`` in all APIs, public and private

**GraphQL**

- The GraphQL layer has been extracted out of Dagit into a separate dagster-graphql package.
- ``startSubplanExecution`` has been replaced by ``executePlan``.
- ``startPipelineExecution`` now supports reexecution of pipeline subsets.

**Dagit**

- It is now possible to reexecute subsets of a pipeline run from Dagit.
- Dagit's `Execute` tab now opens runs in separate browser tabs and a new `Runs` tab allows you to
  browse and view historical runs.
- Dagit no longer scaffolds configuration when creating new `Execute` tabs. This functionality will
  be refined and revisited in the future.
- Dagit's `Explore` tab is more performant on large DAGs.
- The ``dagit -q`` command line flag has been deprecated in favor of a separate command-line
  ``dagster-graphql`` utility.
- The execute button is now greyed out when Dagit is offline.
- The Dagit UI now includes more contextual cues to make the solid in focus and its connections
  more salient.
- Dagit no longer offers to open materializations on your machine. Clicking an on-disk
  materialization now copies the path to your clipboard.
- Pressing Ctrl-Enter now starts execution in Dagit's Execute tab.
- Dagit properly shows List and Nullable types in the DAG view.

**Dagster-Airflow**

- Dagster-Airflow includes functions to dynamically generate containerized (``DockerOperator``-based)
  and uncontainerized (``PythonOperator``-based) Airflow DAGs from Dagster pipelines and config.

**Libraries**

- Dagster integration code with AWS, Great Expectations, Pandas, Pyspark, Snowflake, and Spark
  has been reorganized into a new top-level libraries directory. These modules are now
  importable as ``dagster_aws``, ``dagster_ge``, ``dagster_pandas``, ``dagster_pyspark``,
  ``dagster_snowflake``, and ``dagster_spark``.
- Removed dagster-sqlalchemy and dagma

**Examples**

- Added the event-pipeline-demo, a realistic web event data pipeline using Spark and Scala.
- Added the Pyspark pagerank example, which demonstrates how to incrementally introduce dagster
  into existing data processing workflows.

**Documentation**

- Docs have been expanded, reorganized, and reformatted.

0.3.5
-----
**Dagit**

- Dagit now defaults to ``--watch``; run ``dagit --no-watch`` to disable (process-based)
  autoreloading.

0.3.4
-----

**API Changes**

- ``ExecutionMetadata`` has been renamed to ``RunConfig``
- ``throw_on_user_error`` is no longer a top level argument to ``execute_pipeline``, but
  instead is part of the ``InProcessExecutorConfig``
- We no longer include values of configs in config parsing error exception to prevent
  accidental logging of sensitive information that might be in config files.

**Dagit**

- Show total execution time at the bottom of the execution pane
- Remove extra scrollbars in Windows and Mac with external mouse
- New dynamics for multiple runs in dagit; run history; better tabbing behavior.

**Dagstermill**

- Repo registration is now optional; "Hello, World" examples are now boilerplate free.

0.3.3
-----

**API Changes**

- Removed ``step``, ``environment_config``, ``event_callback``, ``has_event_callback``,
  ``persistence_strategy``, ``events``, and ``execution_metadata properties`` from user-facing
  context objects.
- Removed ``solid_subset`` parameter to ``execute_pipeline``.
- ``check.inst`` and associated methods take type tuples.

**GraphQL**

- ``StartSubplanExecutionInvalidStepsError`` and ``InvalidSubplanExecutionError`` replaced
  with more exact ``StartSubplanExecutionInvalidStepError`` and 
  ``InvalidSubplanMissingInputError``

**Dagit**

- Dagit can launch Jupyter to explore and execute Dagstermill output notebooks.


**Bugfixes**

- #849: Dagit watches fewer files and runs faster.
- #856: Execution steps are displayed in order in Dagit.
- #863, #865: Dagstermill errors are reported.
- #873: Dagit provides visual feedback as soon as pipelines are executed.
- #871: Pipeline validation errors appear in Dagit.
- #872: Dagit logs stream reliably.


0.3.2
-----

**API Changes**

- The ``info`` object passed to transform and expectation functions has been renamed to ``context``.
  All fields that were previously available on the ``info.context`` object are now hoisted to the
  top level ``context`` object. Additionally an alias for ``config`` has been introduced:
  ``solid_config``. So where you would have written ``info.config`` it is now
  ``context.solid_config`` Logging should be done with the top-level property ``context.log``.
  The ``context`` and ``config`` properies on this new context object are deprecated, will warn
  for now, and be eliminated when 0.4.0 is released.
- The ``info`` object passed context and resource creation functions is now named ``init_context``
  by convention.
- PipelineExecutionResult's (returned from execute_pipeline) ``result_list`` property has been
  renamed to ``solid_result_list``
- execute_pipeline_iterator now returns an iterable of ``ExecutionStepEvent`` instead of
  ``SolidExecutionResult``
- Breaking: All arguments named ``environment`` to ``execute_pipeline`` and its variants has
  been renamed to ``environment_dict``.
- Breaking: Types of objects flowed as the first argument to context, resource, transform, and
  expectation functions have been renamed. If you do instanceof checks on these objects, they will
  fail. Property-level compatibility has not changed and should not require code changes.

**GraphQL**

- ``StepResult`` has been renamed to ``StepEvent``.
- ``stepResults`` property on ``startSubplanExecution`` has been renamed to ``stepEvents``.
- ``StepSuccessResult`` is now ``SuccessfulStepOutputEvent``
- ``StepFailureResult`` is now ``StepFailureEvent``
- Added ``UNMARSHAL_INPUT`` and ``MARSHAL_OUTPUT`` values to the ``StepKind`` enumeration.
  Marshalling steps are now implemented as execution steps themselves.

**Dagit**

- Link to output notebook rendered in dagit when dagstermill solids are executed.

**Dagstermill**

- Dagstermill solids now required reduced scaffolding.

**Bugfixes**

- #792: ``execute_pipeline_iterator`` now properly streams results at step-event granularity.
- #820: Unbreak config scaffolding within dagit.



0.3.1
-----

**API Changes**

- New decorator-based ``@resource`` API as a more concise alternative to ``ResourceDefinition``
- Dagster config type system now supports enum types. (``dagster.Enum`` and ``dagster.EnumType``) 
- New top level properties ``resources`` and ``log`` on ``info``.
- The context stack in ``RuntimeExecutionContext`` is no longer modifiable by the user during a
  transform. It has been renamed to ``tags``.
- ``ReentrantInfo`` has been renamed to ``ExecutionMetadata``

**GraphQL**

- GraphQL queries and mutations taking a pipeline name now take both a pipeline name and an optional
  solid subset and have slightly improved call signatures.
- The config and runtime type system split is now reflected in the GraphQL frontend. This was the
  infrastructure piece that allowed the fix to #598. ``runtimeTypeOrError`` and
  ``configTypeOrError`` are now top level fields, and there are ``configTypes`` and 
  ``runtimeTypes`` fields on ``Pipeline``. Top-level field type and types property on ``Pipeline``
  has been eliminated.
- ``StepTag has been renamed to ``StepKind``
- Added s``tartSubplanExecution`` to enable pipeline execution at step subset granularity
- Deprecated ``ExecutionStep.name`` in favor of ``ExecutionStep.key``
- Added ``isBuiltin`` to ``RuntimeType``

**Dagit**

- `Execute` tab now supports partial pipeline execution via a solid selector in the bottom left.
- Dagit execute button is redesigned, indicates running state, and is unpressable when the
  dagit process is dead.
- The config editor now offers autocompletion for enum values.

**Dagstermill**

- Dagstermill has a dramatically improved parameter passing experience and scaffolding and is ready
  for broader consumption.

**Bugfixes**

- #598: Correctly display input and output schemas for types in dagit
- #670: Internal system error "dagster.check.CheckError: Invariant failed. Description: Should not
  be in context" raised when user throwing error during transform. Now the appropriate user error
  should be raised.
- #672: Dagit sometimes hangs (TypeError: unsupported operand type(s) for -: 'float' and
  'NoneType' in console log)
- #575: Improve error messaging by masking anonymous type names
