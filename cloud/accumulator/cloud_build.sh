# If not already configured
gcloud auth configure-docker us-central1-docker.pkg.dev

# Compress codebase
tar -cvzf /tmp/hl-thermo.tgz ../../.

# Submit
GCP_ARTIFACT_REG="us-central1-docker.pkg.dev/hl-therm/hl-therm-models" && \
TAG="$(git rev-parse --short HEAD)" && \
gcloud builds submit /tmp/hl-thermo.tgz --tag $GCP_ARTIFACT_REG/hl-thermo:$TAG