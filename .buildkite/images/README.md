## Publishing new images

1. Put up a diff with the planned changes to the integration images Dockerfile
2. Manually trigger a Buildkite Integration Image pipeline build for the diff tag - see for
   example: https://buildkite.com/dagster/integration-image-builds/builds/19. Hit "New Build", then
   make sure that the value for "Branch" is something like `phabricator/diff/7663` and the value for
   "Commit" is `HEAD`. ("Message" doesn't matter.)
3. After the images successfully publish to ECR, update the diff to set `INTEGRATION_IMAGE_VERSION`
   to the new version (check ECR for the version string, which is the YYYY-mm-ddTHHMMSS when the
   image was created.)
