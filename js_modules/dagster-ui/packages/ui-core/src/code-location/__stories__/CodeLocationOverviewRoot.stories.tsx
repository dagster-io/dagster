import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import {useMemo} from 'react';

import {
  RepositoryLocationLoadStatus,
  buildDagsterLibraryVersion,
  buildRepositoryLocation,
  buildRepositoryMetadata,
  buildWorkspaceLocationEntry,
  buildWorkspaceLocationStatusEntry,
} from '../../graphql/types';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {CodeLocationOverviewRoot} from '../CodeLocationOverviewRoot';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Code Location/CodeLocationOverviewRoot',
  component: CodeLocationOverviewRoot,
} as Meta;

export const Default = () => {
  const repoName = 'foo';
  const locationName = 'bar';

  const now = useMemo(() => Date.now() / 1000, []);
  const locationEntry = buildWorkspaceLocationEntry({
    updatedTimestamp: now,
    name: locationName,
    displayMetadata: [
      buildRepositoryMetadata({
        key: 'image',
        value:
          'whereami.kz.almaty-2.amazonaws.com/whoami:whoami-b0d8eb5c3518ddd5640657075-cb6978e44008',
      }),
      buildRepositoryMetadata({key: 'module_name', value: 'my.cool.module'}),
      buildRepositoryMetadata({key: 'working_directory', value: '/foo/bar/baz'}),
      buildRepositoryMetadata({
        key: 'commit_hash',
        value: '3c88b0248f9b66f2a49e154e4731fe70',
      }),
      buildRepositoryMetadata({
        key: 'url',
        value: 'https://github.com/supercool-org/foobar/tree/3c88b0248f9b66f2a49e154e4731fe70',
      }),
    ],
    locationOrLoadError: buildRepositoryLocation({
      name: locationName,
      dagsterLibraryVersions: [
        buildDagsterLibraryVersion({
          name: 'dagster',
          version: '1.8',
        }),
      ],
    }),
  });

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
