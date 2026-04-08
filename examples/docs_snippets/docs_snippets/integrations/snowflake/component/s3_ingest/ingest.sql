--   1. Create a storage integration in Snowflake:
--        CREATE STORAGE INTEGRATION s3_integration
--          TYPE = EXTERNAL_STAGE
--          STORAGE_PROVIDER = 'S3'
--          STORAGE_AWS_ROLE_ARN = 'arn:aws:iam:::<account>:role/<role>'
--          ENABLED = TRUE
--          STORAGE_ALLOWED_LOCATIONS = ('s3://{{ s3_bucket }}/');
--
--   2. Create an external stage:
--        CREATE STAGE {{ stage_name }}
--          STORAGE_INTEGRATION = s3_integration
--          URL = 's3://{{ s3_bucket }}/{{ s3_prefix }}'
--          FILE_FORMAT = (TYPE = '{{ file_format }}' SKIP_HEADER = 1);

-- highlight-start
-- Create target table if it doesn't exist
CREATE TABLE IF NOT EXISTS {{ database }}.{{ schema }}.{{ table_name }} (
    id              VARCHAR,
    name            VARCHAR,
    email           VARCHAR,
    created_at      TIMESTAMP_NTZ,
    _loaded_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Truncate and reload (full refresh)
TRUNCATE TABLE {{ database }}.{{ schema }}.{{ table_name }};

-- Copy data from S3 stage into Snowflake
COPY INTO {{ database }}.{{ schema }}.{{ table_name }} (id, name, email, created_at)
FROM @{{ stage_name }}/{{ s3_prefix }}
FILE_FORMAT = (TYPE = '{{ file_format }}' SKIP_HEADER = 1)
PATTERN = '{{ file_pattern }}'
ON_ERROR = 'CONTINUE';
-- highlight-end