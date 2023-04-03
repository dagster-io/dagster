import {execSync} from 'child_process';
import {writeFileSync} from 'fs';

import {buildClientSchema, getIntrospectionQuery, printSchema} from 'graphql';

console.log('Downloading schema…');

const TARGET_FILE = './src/graphql/schema.graphql';

// Write schema.graphql in the SDL format, without descriptions. We don't need them here.
const result = execSync(
  `dagster-graphql --ephemeral-instance --empty-workspace -t '${getIntrospectionQuery({
    descriptions: false,
  })}'`,
  {cwd: '../../../../examples/docs_snippets/'},
).toString();
const schemaJson = JSON.parse(result).data;
const sdl = printSchema(buildClientSchema(schemaJson));

console.log('Generating schema.graphql…');

writeFileSync(TARGET_FILE, sdl);

execSync(`yarn prettier --loglevel silent --write ${TARGET_FILE}`, {stdio: 'inherit'});

// Write `possibleTypes.generated.json`, used in prod for `AppCache` and in tests for creating
// a mocked schema.
const possibleTypes: Record<string, string[]> = {};

schemaJson.__schema.types.forEach((supertype: {name: string; possibleTypes: [{name: string}]}) => {
  if (supertype.possibleTypes) {
    possibleTypes[supertype.name] = supertype.possibleTypes.map((subtype) => subtype.name);
  }
});

console.log('Generating possibleTypes.generated.json…');

writeFileSync('./src/graphql/possibleTypes.generated.json', JSON.stringify(possibleTypes));

console.log('Cleaning up existing types…');

execSync('find src -type d -name types | xargs rm -r', {stdio: 'inherit'});

console.log('Generating TypeScript types…');

execSync('yarn graphql-codegen', {stdio: 'inherit'});

console.log('Done!');
