0.3.1

   - Bug fixes
      - #670: Internal system error "dagster.check.CheckError: Invariant failed. Description: Should not be in context" raised when user throwing error during transform. Now the appropriate user error should be raised.
      - #672: Dagit sometimes hangs (TypeError: unsupported operand type(s) for -: 'float' and 'NoneType' in console log)

   - API Additions:
      - New decorated-based @resource API as a more concise alternative to ResourceDefinition
