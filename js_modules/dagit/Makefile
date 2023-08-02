dev_webapp:
	REACT_APP_BACKEND_ORIGIN="http://127.0.0.1:3333" yarn start

generate-graphql:
	yarn workspace @dagster-io/ui-core generate-graphql

generate-perms:
	yarn workspace @dagster-io/ui-core generate-perms

ts:
	yarn workspace @dagster-io/app-oss ts && yarn workspace @dagster-io/ui-core ts && yarn workspace @dagster-io/ui ts

lint:
	yarn workspace @dagster-io/app-oss lint && yarn workspace @dagster-io/ui-core lint && yarn workspace @dagster-io/ui lint

test:
	yarn workspace @dagster-io/ui-core jest && yarn workspace @dagster-io/ui jest

jest:
	yarn workspace @dagster-io/ui-core jest && yarn workspace @dagster-io/ui jest
