docker build -t pipes-materialize:latest -f Dockerfile.materialize .
docker build -t pipes-check:latest -f Dockerfile.check .
kind load docker-image pipes-materialize pipes-materialize
kind load docker-image pipes-check pipes-check