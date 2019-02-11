0.3.2

   - New features
      - Link to output notebook rendered in dagit when dagstermill solids are executed.

   - API Additions and changes
      - The ``info`` object passed to transform functions has been renamed to ``context``. All fields that were previously
        available on the ``info.context`` object are now hoisted to the top level ``context`` object. Additionally an alias
        for ``config`` has been introduced: ``solid_config``. So where you would have written ``info.config`` it is now
        ``context.solid_config`` Logging should be done with the top-level property ``context.log``. The ``context``
        and ``config`` properies on this new context object are deprecated, will warn for now, and be eliminated
        when 0.4.0 is released.
      - PipelineExecutionResult's (returned from execute_pipeline)
        ``result_list`` property has been renaming to ``solid_result_list``
      - execute_pipeline_iterator now returns an iterable of ExecutionStepEvent instead of SolidExecutionResult

   - Bug fixes
      - #792: execute_pipeline_iterator now properly streams results at step-event granularity.

   - GraphQL Schema Changes
      - ``StepResult`` has been renamed to ``StepEvent``.
      - ``stepResults`` property on ``startSubplanExecution`` has been renamed to ``stepEvents``.
      - ``StepSuccessResult`` is now ``SuccessfulStepOutputEvent``
      - ``StepFailureResult`` is now ``StepFailureEvent``
      - Added ``UNMARSHAL_INPUT`` and ``MARSHAL_OUTPUT`` values to the ``StepKind`` enumeration. Marshalling steps are now
        implemented as execution steps themselves.


0.3.1

   - New Features
      - Dagit: Execute tab now supports partial pipeline execution via a solid selector in the bottom left.
      - Dagstermill has a dramatically improved parameter passing experience and scaffolding and is ready for broader consumption.
      - Dagit: Dagit execute button is redesigned, indicates running state, and is unpressable when the dagit process is dead.
      - Dagit: The config editor now offers autocompletion for enum values.

   - Bug fixes
      - #598: Correctly display input and output schemas for types in dagit
      - #670: Internal system error "dagster.check.CheckError: Invariant failed. Description: Should not be in context" raised when user throwing error during transform. Now the appropriate user error should be raised.
      - #672: Dagit sometimes hangs (TypeError: unsupported operand type(s) for -: 'float' and 'NoneType' in console log)
      - #575: Improve error messaging by masking anonymous type names

   - API Additions and Changes
      - New decorated-based @resource API as a more concise alternative to ResourceDefinition
      - Dagster config type system now supports enum types. (dagster.Enum and dagster.EnumType) 
      - New top level properties ``resources`` and ``log`` on info.
      - The context stack in RuntimeExecutionContext is no longer modify-able by the user during a transform. It has been renamed to 'tags'.
      - ReentrantInfo has been renamed to ExecutionMetadata

   - GraphQL Schema Changes
      - GraphQL queries and mutations taking a pipeline name now take both a pipeline name and an optional
        solid subset and have slightly improved call signatures.
      - The config and runtime type system split is now reflected in the GraphQL frontend. This was the infrastructure
        piece that allowed the fix to #598. runtimeTypeOrError, configTypeOrError are now top level fields, and there
        are configTypes and runtimeTypes fields on Pipeline. Top-level field type and types property on Pipeline has
        been eliminated.
      - StepTag has been renamed to StepKind
      - Added startSubplanExecution to enable pipeline execution at step subset granularity
      - Deprecated ExecutionStep.name in favor of ExecutionStep.key
      - Added isBuiltin to RuntimeType
