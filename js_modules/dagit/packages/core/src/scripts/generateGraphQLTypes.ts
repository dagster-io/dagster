import {execSync} from 'child_process';
import {writeFileSync} from 'fs';

import {buildClientSchema, getIntrospectionQuery, printSchema} from 'graphql';

console.log('Downloading schema...');

const TARGET_FILE = './src/graphql/schema.graphql';

// https://github.com/dagster-io/dagster/issues/2623
const result = execSync(
  `dagster-graphql --ephemeral-instance --empty-workspace -t '${getIntrospectionQuery({
    descriptions: false,
  })}'`,
  {cwd: '../../../../examples/docs_snippets/'},
).toString();

const schemaJson = JSON.parse(result).data;

// Write schema.graphql in the SDL format
const sdl = printSchema(buildClientSchema(schemaJson));

console.log('Generating schema.graphql...');

writeFileSync(TARGET_FILE, sdl);

// Write `possibleTypes.generated.json`, used in prod for `AppCache` and in tests for creating
// a mocked schema.
const possibleTypes = {};

schemaJson.__schema.types.forEach((supertype: {name: string; possibleTypes: [{name: string}]}) => {
  if (supertype.possibleTypes) {
    possibleTypes[supertype.name] = supertype.possibleTypes.map((subtype) => subtype.name);
  }
});

console.log('Generating possibleTypes.generated.json...');

writeFileSync('./src/graphql/possibleTypes.generated.json', JSON.stringify(possibleTypes));

console.log('Generating TypeScript types...');

execSync(
  `find src -type d -name types | xargs rm -r && yarn apollo codegen:generate --includes "./src/**/*.tsx" --target typescript types --localSchemaFile ${TARGET_FILE} --globalTypesFile ./src/types/globalTypes.ts`,
  {stdio: 'inherit'},
);

execSync(`yarn prettier --loglevel silent --write ${TARGET_FILE}`, {stdio: 'inherit'});

console.log('Done!');
