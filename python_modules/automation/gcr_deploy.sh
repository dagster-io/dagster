# See: https://cloud.google.com/container-registry/docs/quickstart

docker build -t generate_synthetic_events .

TAG=`date '+%Y-%m-%d-%H-%M-%S'`

echo "Pushing container with tags: [${TAG}, latest]"

docker tag generate_synthetic_events "gcr.io/${GCP_PROJECT_ID}/generate_synthetic_events:${TAG}"
docker tag generate_synthetic_events "gcr.io/${GCP_PROJECT_ID}/generate_synthetic_events:latest"
docker push "gcr.io/${GCP_PROJECT_ID}/generate_synthetic_events:${TAG}"
docker push "gcr.io/${GCP_PROJECT_ID}/generate_synthetic_events:latest"
