import {Box} from '@dagster-io/ui';
import * as React from 'react';

import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OpsRoot} from '../ops/OpsRoot';

import {WorkspaceHeader} from './WorkspaceHeader';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {RepoAddress} from './types';

export const WorkspaceOpsRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const repoName = repoAddressAsHumanString(repoAddress);
  useDocumentTitle(`Ops: ${repoName}`);

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <WorkspaceHeader repoAddress={repoAddress} tab="ops" />
      <OpsRoot repoAddress={repoAddress} />
    </Box>
  );
};
