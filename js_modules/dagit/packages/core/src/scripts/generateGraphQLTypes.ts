import {execSync} from 'child_process';
import {writeFileSync} from 'fs';

import {buildClientSchema, getIntrospectionQuery, printSchema} from 'graphql';

console.log('Downloading schema...');

const TARGET_FILE = './src/graphql/schema.graphql';

// https://github.com/dagster-io/dagster/issues/2623
// Initially, write schema.graphql in the SDL format, without descriptions
// Otherwise, the generated types in Typescript would also have descriptions.
const result = execSync(
  `dagster-graphql --ephemeral-instance --empty-workspace -t '${getIntrospectionQuery({
    descriptions: false,
  })}'`,
  {cwd: '../../../../examples/docs_snippets/'},
).toString();
const schemaJson = JSON.parse(result).data;
const sdl = printSchema(buildClientSchema(schemaJson));

console.log('Generating schema.graphql without descriptions...');

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

// https://github.com/dagster-io/dagster/issues/2623
// Finally, write schema.graphql in the SDL format, with descriptions
const resultWithDescriptions = execSync(
  `dagster-graphql --ephemeral-instance --empty-workspace -t '${getIntrospectionQuery()}'`,
  {cwd: '../../../../examples/docs_snippets/'},
).toString();
const schemaJsonWithDescriptions = JSON.parse(resultWithDescriptions).data;
const sdlWithDescriptions = printSchema(buildClientSchema(schemaJsonWithDescriptions));

console.log('Generating schema.graphql with descriptions...');

writeFileSync(TARGET_FILE, sdlWithDescriptions);

execSync(`yarn prettier --loglevel silent --write ${TARGET_FILE}`, {stdio: 'inherit'});

console.log('Done!');
