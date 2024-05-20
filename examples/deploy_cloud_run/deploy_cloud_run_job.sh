#!/bin/bash

PROJECT_ID="" # add your project id
FOLDER_NAME="dagster"
REGION="" # add your region
SERVICE_ACCOUNT_EMAIL="" # add your service account
PIPELINE_BASE_DIR="./cloud_run_pipeline"

for PIPELINE_DIR in $PIPELINE_BASE_DIR/*; do
    if [ -d "$PIPELINE_DIR" ]; then
        PIPELINE_NAME=$(basename "$PIPELINE_DIR")
        IMAGE_NAME="dagster-$PIPELINE_NAME"
        JOB_NAME="${PIPELINE_NAME}-job"

        echo "Building Docker image for $PIPELINE_NAME..."
        docker build -t $IMAGE_NAME -f Dockerfile --build-arg PIPELINE_DIR=$PIPELINE_DIR --platform=linux/amd64 .

        echo "Tagging Docker image for $PIPELINE_NAME..."
        docker tag $IMAGE_NAME $REGION-docker.pkg.dev/$PROJECT_ID/$FOLDER_NAME/$IMAGE_NAME:latest

        echo "Pushing Docker image for $PIPELINE_NAME to Google Artifact Registry..."
        docker push $REGION-docker.pkg.dev/$PROJECT_ID/$FOLDER_NAME/$IMAGE_NAME:latest

        echo "Creating Cloud Run job for $PIPELINE_NAME..."
        gcloud beta run jobs create $JOB_NAME \
            --image=$REGION-docker.pkg.dev/$PROJECT_ID/$FOLDER_NAME/$IMAGE_NAME:latest \
            --region=$REGION \
            --service-account=$SERVICE_ACCOUNT_EMAIL \
            --project=$PROJECT_ID \
            --set-secrets="DAGSTER_PG_HOST=DAGSTER_PG_HOST:latest,DAGSTER_PG_USERNAME=DAGSTER_PG_USERNAME:latest,DAGSTER_PG_PASSWORD=DAGSTER_PG_PASSWORD:latest,DAGSTER_PG_DB=DAGSTER_PG_DB:latest"
    fi
done
