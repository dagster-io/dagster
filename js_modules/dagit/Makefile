dev_webapp:
	REACT_APP_GRAPHQL_URI="ws://localhost:3333/graphql" yarn start

download-schema:
	REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn workspace @dagit/core download-schema

generate-types: download-schema
	yarn workspace @dagit/core generate-types

ts:
	yarn workspace @dagit/app ts && yarn workspace @dagit/core ts

lint:
	yarn workspace @dagit/app lint && yarn workspace @dagit/core lint

test:
	yarn workspace @dagit/core test

jest:
	yarn workspace @dagit/core jest
