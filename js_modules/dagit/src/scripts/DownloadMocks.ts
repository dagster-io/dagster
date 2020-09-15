import {execSync} from 'child_process';
import {addTypenameToDocument} from 'apollo-utilities';
import {print} from 'graphql/language/printer';
import path from 'path';
import fs from 'fs';

/*
Why is this script structured as a Jest test? Jest goes to great lengths to
setup a NodeJS execution environment that also mimics a browser, so we can read/
write to the filesystem but ALSO load all of the application code (and retrieve
the query objects), etc. We could set all this up (new tsconfig, jsdom, etc.) but
leveraging Jest is easiest.
*/

// collect mocks from various tests in the codebase
import {MOCKS as SVGMocks} from '../__tests__/graph/SVGMocks';
import {MOCKS as AppMocks} from '../__tests__/AppMocks';

const dagsterRoot = path.resolve(path.join(__dirname, '..', '..', '..', '..'));

it(`builds mocks`, () => {
  for (const mock of [...SVGMocks, ...AppMocks]) {
    const query = print(addTypenameToDocument(mock.query))
      .replace(/[\n\r]/g, '')
      .replace(/[ ][ ]+/g, ' ');
    const vars = mock.variables ? `-v '${JSON.stringify(mock.variables)}'` : '';
    const repo = `${dagsterRoot}/${mock.repo || 'examples/airline_demo'}/${
      mock.workspace ? 'workspace' : 'repository'
    }.yaml`;

    execSync(`dagster-graphql -y ${repo} -t '${query}' ${vars} > ${mock.filepath}`);

    if (JSON.parse(fs.readFileSync(mock.filepath).toString()).errors) {
      throw new Error(`Failed to generate ${mock.filepath}. See file for GraphQL error.`);
    }
    console.log(`Saved ${mock.filepath}`);
  }

  console.log(`Done.`);
});
