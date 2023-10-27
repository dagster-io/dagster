dev_webapp:
	NEXT_PUBLIC_BACKEND_ORIGIN="http://127.0.0.1:3333" yarn start

generate-graphql:
	yarn workspace @dagster-io/ui-core generate-graphql

generate-perms:
	yarn workspace @dagster-io/ui-core generate-perms

ts:
	yarn workspace @dagster-io/app-oss ts && yarn workspace @dagster-io/ui-core ts && yarn workspace @dagster-io/ui-components ts

lint:
	yarn workspace @dagster-io/app-oss lint && yarn workspace @dagster-io/ui-core lint && yarn workspace @dagster-io/ui-components lint

test:
	yarn workspace @dagster-io/ui-core jest-all-silent && yarn workspace @dagster-io/ui-components jest-all-silent

jest:
	yarn workspace @dagster-io/ui-core jest-all-silent && yarn workspace @dagster-io/ui-components jest-all-silent


