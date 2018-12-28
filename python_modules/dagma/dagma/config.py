"""Dagma config."""

DEFAULT_S3_BUCKET = 'dagster-lambda-execution'

DEFAULT_PUT_OBJECT_KWARGS = {
    'ACL': 'bucket-owner-full-control',
    'StorageClass': 'STANDARD',
}

DEFAULT_STORAGE_CONFIG = {
    'put_object_kwargs': DEFAULT_PUT_OBJECT_KWARGS,
}

ASSUME_ROLE_POLICY_DOCUMENT = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"""

BUCKET_POLICY_DOCUMENT_TEMPLATE = """{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Principal": {{
                "AWS": "{role_arn}"
            }},
            "Action": "*",
            "Resource": [
                "{bucket_arn}",
                "{bucket_arn}/*"
            ]
        }}
    ]
}}
"""

DEFAULT_RUNTIME_BUCKET = 'dagma-runtime'

PYTHON_DEPENDENCIES = [
    'boto3', 'cloudpickler', 'git+ssh://git@github.com/dagster-io/dagster.git'
    '@lambda_engine#egg=dagma&subdirectory=python_modules/dagma'
]
