from .schema import df, trips_schema

trips_schema.validate(df)
# => SchemaError: non-nullable series 'end_time' contains null values:
# => 22   NaT
# => 43   NaT
