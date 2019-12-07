## Credentials for push

You must set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, **and** `AWS_ACCOUNT_ID` to push
integration images to ECR. You must also set ECR creds:

    aws ecr get-login --no-include-email --region us-west-1 | sh
