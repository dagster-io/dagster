
0.3.1

   - New Features
      - Dagit's Execute tab now supports partial pipeline execution via a solid selector in the bottom left.
   
   - Bug fixes
      - #670: Internal system error "dagster.check.CheckError: Invariant failed. Description: Should not be in context" raised when user throwing error during transform. Now the appropriate user error should be raised.
      - #672: Dagit sometimes hangs (TypeError: unsupported operand type(s) for -: 'float' and 'NoneType' in console log)

   - API Additions
      - New decorated-based @resource API as a more concise alternative to ResourceDefinition
      - Dagster config type system now supports enum types. (dagster.Enum and dagster.EnumType)

   - Notes
      - GraphQL queries and mutations taking a pipeline name now take both a pipeline name and an optional
        solid subset and have slightly improved call signatures.

