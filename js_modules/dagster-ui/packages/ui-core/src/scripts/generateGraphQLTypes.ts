import {execSync} from 'child_process';
import {readFileSync, readdirSync, statSync, writeFileSync} from 'fs';
import path from 'path';

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

execSync(`yarn prettier --log-level silent --write ${TARGET_FILE}`, {stdio: 'inherit'});

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

function exportHashesAsVersionVariables() {
  const CLIENT_JSON_PATH = './client.json';
  const SRC_DIR = './src';

  // Load the client.json which contains the hashes for each query/mutation
  const queryHashMap = JSON.parse(readFileSync(CLIENT_JSON_PATH, 'utf-8'));

  // Function to recursively find all .types.ts files
  const findTypeFiles = (dir: string): string[] => {
    let results: string[] = [];
    const list = readdirSync(dir);

    list.forEach((file) => {
      const filePath = path.join(dir, file);
      const stat = statSync(filePath);

      if (stat && stat.isDirectory()) {
        // Recursively search in subdirectories
        results = results.concat(findTypeFiles(filePath));
      } else if (filePath.endsWith('.types.ts')) {
        results.push(filePath);
      }
    });

    return results;
  };

  // Function to process .types.ts files and append version hashes
  const processTypeFiles = (files: string[], queryHashMap: Record<string, string>) => {
    files.forEach((filePath) => {
      let content = readFileSync(filePath, 'utf-8');

      // Look for the query/mutation type name in the file
      Object.entries(queryHashMap).forEach(([operationName, hash]) => {
        const typeRegex = new RegExp(`export type ${operationName}`, 'g');

        if (typeRegex.test(content)) {
          // Add the version constant
          const versionConstant = `\nexport const ${operationName}Version = '${hash}';\n`;

          // Append the version constant to the file if it doesn't already exist
          if (!content.includes(`${operationName}Version`)) {
            content += versionConstant;
            writeFileSync(filePath, content);
          }
        }
      });
    });
  };

  // Recursively find all `.types.ts` files in the src directory
  const typeFiles = findTypeFiles(SRC_DIR);

  // Process all `.types.ts` files to find queries/mutations and add version constants
  processTypeFiles(typeFiles, queryHashMap);

  console.log('Type files updated with version hashes.');
}

exportHashesAsVersionVariables();
