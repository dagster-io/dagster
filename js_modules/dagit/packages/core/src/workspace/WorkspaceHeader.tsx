import {PageHeader, Box, Heading, Colors} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {WorkspaceTabs} from './WorkspaceTabs';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';

export const WorkspaceHeader: React.FC<{repoAddress: RepoAddress; tab: string}> = ({
  repoAddress,
  tab,
}) => {
  return (
    <PageHeader
      title={
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Heading>
            <Link to="/workspace" style={{color: Colors.Dark}}>
              Workspace
            </Link>
          </Heading>
          <Heading>/</Heading>
          <Heading style={{color: Colors.Gray600}}>{repoAddressAsString(repoAddress)}</Heading>
        </Box>
      }
      tabs={<WorkspaceTabs repoAddress={repoAddress} tab={tab} />}
    />
  );
};
