
0.3.1

   - New Features
      - Dagit: Execute tab now supports partial pipeline execution via a solid selector in the bottom left.
      - Dagstermill has a dramatically improved parameter passing experience and scaffolding and is ready for broader consumption.
      - Dagit: Dagit execute button is redesigned, indicates running state, and is unpressable when the dagit process is dead.
   
   - Bug fixes
      - #598: Correctly display input and output schemas for types in dagit
      - #670: Internal system error "dagster.check.CheckError: Invariant failed. Description: Should not be in context" raised when user throwing error during transform. Now the appropriate user error should be raised.
      - #672: Dagit sometimes hangs (TypeError: unsupported operand type(s) for -: 'float' and 'NoneType' in console log)

   - API Additions and Changes
      - New decorated-based @resource API as a more concise alternative to ResourceDefinition
      - Dagster config type system now supports enum types. (dagster.Enum and dagster.EnumType) 
      - New top level properties `resources` and `log` on info.
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
