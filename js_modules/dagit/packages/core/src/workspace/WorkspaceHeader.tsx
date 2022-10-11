import {QueryResult} from '@apollo/client';
import {PageHeader, Box, Heading, Colors, Button, Icon} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {QueryRefreshState} from '../app/QueryRefresh';
import {ReloadRepositoryLocationButton} from '../nav/ReloadRepositoryLocationButton';

import {WorkspaceTabs} from './WorkspaceTabs';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';

interface Props<TData> {
  repoAddress: RepoAddress;
  tab: string;
  refreshState?: QueryRefreshState;
  queryData?: QueryResult<TData, any>;
}

export const WorkspaceHeader = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {repoAddress, tab, refreshState, queryData} = props;

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
      tabs={
        <WorkspaceTabs
          repoAddress={repoAddress}
          tab={tab}
          refreshState={refreshState}
          queryData={queryData}
        />
      }
      right={
        <ReloadRepositoryLocationButton location={repoAddress.location}>
          {({tryReload, reloading}) => {
            return (
              <Button
                onClick={() => tryReload()}
                loading={reloading}
                icon={<Icon name="refresh" />}
              >
                Reload repository location
              </Button>
            );
          }}
        </ReloadRepositoryLocationButton>
      }
    />
  );
};
