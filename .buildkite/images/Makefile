py27 = 2.7.17
py36 = 3.6.10
py37 = 3.7.6
py38 = 3.8.1

####################################################################################################
# Update snapshots
####################################################################################################
snap:
	./integration/snapshot-update.sh

####################################################################################################
# Buildkite images
####################################################################################################
build-integration-38:
	./integration/build.sh $(py38) $(VERSION)

push-integration-38:
	./integration/push.sh $(py38) $(VERSION)

build-integration-37:
	./integration/build.sh $(py37) $(VERSION)

push-integration-37:
	./integration/push.sh $(py37) $(VERSION)

build-integration-36:
	./integration/build.sh $(py36) $(VERSION)

push-integration-36:
	./integration/push.sh $(py36) $(VERSION)

build-integration-27:
	./integration/build.sh $(py27) $(VERSION)

push-integration-27:
	./integration/push.sh $(py27) $(VERSION)

build-integration: build-integration-38 build-integration-37 build-integration-36 build-integration-27
push-integration: push-integration-38 push-integration-37 push-integration-36 push-integration-27
