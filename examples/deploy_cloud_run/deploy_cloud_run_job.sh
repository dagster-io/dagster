#!/bin/bash

PROJECT_ID=""
IMAGE_NAME="dagster"
FOLDER_NAME="dagster"
REGION=""
JOB_NAME="dagster-job"

echo "Building Docker image..."
docker build -t $IMAGE_NAME . --platform=linux/amd64

echo "Tag image"
docker tag $IMAGE_NAME $REGION-docker.pkg.dev/$PROJECT_ID/$FOLDER_NAME/$IMAGE_NAME:latest

echo "Pushing image to Google Artifact Registry..."
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$FOLDER_NAME/$IMAGE_NAME:latest

echo "Creating Cloud Run job..."
gcloud beta run jobs create $JOB_NAME \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/$FOLDER_NAME/$IMAGE_NAME:latest \
    --region=$REGION \
    --service-account=$SERVICE_ACCOUNT \
    --project=$PROJECT_ID \
    --set-secrets="DAGSTER_PG_HOST=DAGSTER_PG_HOST:latest,DAGSTER_PG_USERNAME=DAGSTER_PG_USERNAME:latest,DAGSTER_PG_PASSWORD=DAGSTER_PG_PASSWORD:latest,DAGSTER_PG_DB=DAGSTER_PG_DB:latest"