import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import {useMemo} from 'react';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';

import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {CodeLocationDefinitionsRoot} from '../CodeLocationDefinitionsRoot';
import {
  buildSampleOpsRootQuery,
  buildSampleRepository,
  buildSampleRepositoryAssetsQuery,
  buildSampleRepositoryGraphsQuery,
} from '../__fixtures__/CodeLocationPages.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Code Location/CodeLocationDefinitionsRoot',
  component: CodeLocationDefinitionsRoot,
} as Meta;

export const Default = () => {
  const repoName = 'foo';
  const locationName = 'bar';
  const repoAddress = buildRepoAddress(repoName, locationName);

  // const now = useMemo(() => Date.now() / 1000, []);
  const repository = buildSampleRepository({
    name: repoName,
    jobCount: 500,
    scheduleCount: 200,
    sensorCount: 200,
    resourceCount: 100,
  });

  const mocks = useMemo(
    () => [
      buildSampleOpsRootQuery({repoAddress, opCount: 500}),
      buildSampleRepositoryGraphsQuery({repoAddress, jobCount: 500, opCount: 500}),
      buildSampleRepositoryAssetsQuery({repoAddress, groupCount: 10, assetsPerGroup: 100}),
    ],
    [repoAddress],
  );

  return (
    <RecoilRoot>
      <MemoryRouter initialEntries={[workspacePathFromAddress(repoAddress, '/jobs')]}>
        <MockedProvider mocks={mocks}>
          <div style={{height: '500px', overflow: 'hidden'}}>
            <CodeLocationDefinitionsRoot
              repoAddress={buildRepoAddress(repoName, locationName)}
              repository={repository}
            />
          </div>
        </MockedProvider>
      </MemoryRouter>
    </RecoilRoot>
  );
};
