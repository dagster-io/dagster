import {execSync} from 'child_process';
import {writeFileSync} from 'fs';

import {buildClientSchema, getIntrospectionQuery, printSchema} from 'graphql';

const pyVer = execSync('python3 --version').toString();
const verMatch = pyVer.match(/Python ([\d.]*)/);
if (!(verMatch != null && verMatch.length >= 2 && parseFloat(verMatch[1]) >= 3.6)) {
  const errMsg =
    pyVer !== '' ? pyVer : 'nothing on stdout indicating no python or a version earlier than 3.4';
  throw new Error(`Must use Python version >= 3.6 got ${errMsg}`);
}

console.log('Downloading schema...');

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

writeFileSync('./src/graphql/schema.graphql', sdl);

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
  'find src -type d -name types | xargs rm -r && yarn apollo codegen:generate --includes "./src/**/*.tsx" --target typescript types --localSchemaFile ./src/graphql/schema.graphql --globalTypesFile ./src/types/globalTypes.ts && python3 append_generated.py',
  {stdio: 'inherit'},
);

console.log('Done!');
