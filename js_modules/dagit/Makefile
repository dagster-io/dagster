dev_webapp:
	REACT_APP_GRAPHQL_URI="ws://localhost:3333/graphql" yarn start

generate-graphql:
	yarn workspace @dagit/core generate-graphql

ts:
	yarn workspace @dagit/app ts && yarn workspace @dagit/core ts

lint:
	yarn workspace @dagit/app lint && yarn workspace @dagit/core lint

test:
	yarn workspace @dagit/core jest

jest:
	yarn workspace @dagit/core jest
