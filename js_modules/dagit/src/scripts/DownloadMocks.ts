import { execSync } from "child_process";
import { print } from "graphql/language/printer";
import path from "path";

/*
Why is this script structured as a Jest test? Jest goes to great lengths to
setup a NodeJS execution environment that also mimics a browser, so we can read/
write to the filesystem but ALSO load all of the application code (and retrieve
the query objects), etc. We could set all this up (new tsconfig, jsdom, etc.) but
leveraging Jest is easiest.
*/

// collect mocks from various tests in the codebase
import { MOCKS as SVGMocks } from "../__tests__/graph/SVGMocks";
import { MOCKS as AppMocks } from "../__tests__/AppMocks";
import { START_PIPELINE_EXECUTION_MUTATION } from "../execute/PipelineExecutionContainer";
import { DocumentNode } from "graphql";

const dagsterRoot = path.resolve(path.join(__dirname, "..", "..", "..", ".."));

function buildArgs(input: {
  repo?: string;
  query: DocumentNode;
  variables?: { [key: string]: any };
}) {
  const query = print(input.query)
    .replace(/[\n\r]/g, "")
    .replace(/[ ][ ]+/g, " ");
  const vars = input.variables ? `-v '${JSON.stringify(input.variables)}'` : "";
  const repo = `${dagsterRoot}/${input.repo || "examples"}/repository.yaml`;

  return `--log --log-dir="/tmp/dagster" -y ${repo} -t '${query}' ${vars}`;
}

it(`builds mocks`, () => {
  // Run a pipeline to generate data that will be returned in the runs queries
  execSync(
    `dagster-graphql ${buildArgs({
      query: START_PIPELINE_EXECUTION_MUTATION,
      variables: {
        executionParams: {
          environmentConfigData: {},
          selector: { name: "log_spew", solidSubset: null },
          mode: "default"
        }
      }
    })}`
  );

  for (const mock of [...SVGMocks, ...AppMocks]) {
    execSync(`dagster-graphql ${buildArgs(mock)} > ${mock.filepath}`);
    console.log(`Saved ${mock.filepath}`);
  }

  console.log(`Done.`);
});
