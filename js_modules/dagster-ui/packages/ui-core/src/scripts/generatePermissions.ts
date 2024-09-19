import {execSync} from 'child_process';
import {writeFileSync} from 'fs';

console.log('Downloading permissions...');

const TARGET_FILE = './src/graphql/permissions.json';

const result = execSync(
  `dagster-graphql --ephemeral-instance --empty-workspace -t 'query { permissions { permission } }'`,
  {cwd: '../../../../examples/docs_snippets/'},
).toString();

const permissionJson = JSON.parse(result).data.permissions;

console.log('Generating permissions.json...');

writeFileSync(TARGET_FILE, JSON.stringify(permissionJson));

console.log('Done!');
