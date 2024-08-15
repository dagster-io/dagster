import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';

import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {CodeLocationDefinitionsRoot} from '../CodeLocationDefinitionsRoot';
import {buildSampleRepository} from '../__fixtures__/CodeLocationPages.fixtures';

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

  return (
    <RecoilRoot>
      <MemoryRouter initialEntries={[workspacePathFromAddress(repoAddress, '/jobs')]}>
        <MockedProvider>
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
