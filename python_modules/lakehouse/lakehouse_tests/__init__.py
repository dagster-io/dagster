'''This is set of test cases used to explore the different properties of lakehouse
that we want

Test 1: test_basic_pyspark_lakehouse.py
    - It uses the prefab PySparkMemLakehouse lakehouse in order 
Test 2: test_pyspark_custom_url_scheme.py
    - Implements custom lakehouse (ByFeatureParquetLakehouse) to do
    custom url schema. This lakehouse variant relies on every
    solid having a 'feature_area' metadata entry
Test 3: test_typed_pyspark_lakehouse.py
    - Demonstrates what a typed variant of this would look like.
    - Currently types are only used to generate documetation
    Additional features to add:
        - Smoke tests that create empty dataframes automatically and
        provide schema
        - Actually do validation and perhaps coercion on output dataframes
        - Do pre-execution validation on the types.

Additional tests/use cases to add:

- A pure snowflake variant of this. Note that snowflake has a copy-on-write
database feature that kt is planning on using to allow for namespacing
so that each dev has a schema and for testing etc.
- A variant that allows that spark lakehouse to persist configurably in s3, snowflake,
or both.
- A variant that allows computation to be mixed between spark and snowflake. Snowflake
solids would optionally point to a file on disk that analysts could edit directly
without mucking with python.
'''
