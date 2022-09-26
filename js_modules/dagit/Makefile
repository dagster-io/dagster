dev_webapp:
	REACT_APP_BACKEND_ORIGIN="http://127.0.0.1:3333" yarn start

generate-graphql:
	yarn workspace @dagster-io/dagit-core generate-graphql

generate-perms:
	yarn workspace @dagster-io/dagit-core generate-perms

ts:
	yarn workspace @dagster-io/dagit-app ts && yarn workspace @dagster-io/dagit-core ts && yarn workspace @dagster-io/ui ts

lint:
	yarn workspace @dagster-io/dagit-app lint && yarn workspace @dagster-io/dagit-core lint && yarn workspace @dagster-io/ui lint

test:
	yarn workspace @dagster-io/dagit-core jest && yarn workspace @dagster-io/ui jest

jest:
	yarn workspace @dagster-io/dagit-core jest && yarn workspace @dagster-io/ui jest
