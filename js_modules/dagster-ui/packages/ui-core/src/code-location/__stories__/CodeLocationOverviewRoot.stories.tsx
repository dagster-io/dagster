import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import {useMemo} from 'react';

import {RepositoryLocationLoadStatus, buildWorkspaceLocationStatusEntry} from '../../graphql/types';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {CodeLocationOverviewRoot} from '../CodeLocationOverviewRoot';
import {buildEmptyWorkspaceLocationEntry} from '../__fixtures__/CodeLocationPages.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Code Location/CodeLocationOverviewRoot',
  component: CodeLocationOverviewRoot,
} as Meta;

export const Default = () => {
  const repoName = 'foo';
  const locationName = 'bar';

  const now = useMemo(() => Date.now() / 1000, []);
  const locationEntry = buildEmptyWorkspaceLocationEntry({time: now, locationName});

  const locationStatus = buildWorkspaceLocationStatusEntry({
    loadStatus: RepositoryLocationLoadStatus.LOADED,
    updateTimestamp: now,
  });

  return (
    <MockedProvider>
      <CodeLocationOverviewRoot
        repoAddress={buildRepoAddress(repoName, locationName)}
        locationEntry={locationEntry}
        locationStatus={locationStatus}
      />
    </MockedProvider>
  );
};
