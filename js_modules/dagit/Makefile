dev_webapp:
	REACT_APP_GRAPHQL_URI="ws://localhost:3333/graphql" yarn start

download-schema:
	REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn run download-schema

generate-types: download-schema
	yarn run generate-types

ts:
	yarn run ts

prettier:
	yarn prettier

test:
	yarn run test

update-snapshots:
	yarn run jest -u

jest:
	yarn run jest
