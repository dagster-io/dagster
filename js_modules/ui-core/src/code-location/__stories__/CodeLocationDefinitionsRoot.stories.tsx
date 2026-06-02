import {MockedProvider} from '@apollo/client/testing';
import {useMemo} from 'react';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';

import {WorkspaceContext} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {CodeLocationDefinitionsRoot} from '../CodeLocationDefinitionsRoot';
import {
  buildEmptyWorkspaceLocationEntry,
  buildSampleOpsRootQuery,
  buildSampleRepository,
  buildSampleRepositoryGraphsQuery,
} from '../__fixtures__/CodeLocationPages.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Code Location/CodeLocationDefinitionsRoot',
  component: CodeLocationDefinitionsRoot,
};

export const Default = () => {
  const repoName = 'foo';
  const locationName = 'bar';
  const repoAddress = buildRepoAddress(repoName, locationName);

  const repository = buildSampleRepository({
    name: repoName,
    jobCount: 500,
    scheduleCount: 200,
    sensorCount: 200,
    resourceCount: 100,
  });

  const locationEntry = buildEmptyWorkspaceLocationEntry({
    time: Date.now() / 1000,
    locationName,
  });

  const mocks = useMemo(
    () => [
      buildSampleOpsRootQuery({repoAddress, opCount: 500}),
      buildSampleRepositoryGraphsQuery({repoAddress, jobCount: 500, opCount: 500}),
    ],
    [repoAddress],
  );

  return (
    <RecoilRoot>
      <MemoryRouter initialEntries={[workspacePathFromAddress(repoAddress, '/jobs')]}>
        <MockedProvider mocks={mocks}>
          <WorkspaceContext.Provider
            value={{
              allRepos: [],
              visibleRepos: [],
              data: {},
              refetch: async () => {},
              toggleVisible: () => {},
              loadingNonAssets: false,
              loadingAssets: false,
              assetEntries: {},
              locationEntries: [locationEntry],
              locationStatuses: {},
              setVisible: () => {},
              setHidden: () => {},
            }}
          >
            <div style={{height: '500px', overflow: 'hidden'}}>
              <CodeLocationDefinitionsRoot
                repoAddress={buildRepoAddress(repoName, locationName)}
                repository={repository}
              />
            </div>
          </WorkspaceContext.Provider>
        </MockedProvider>
      </MemoryRouter>
    </RecoilRoot>
  );
};
