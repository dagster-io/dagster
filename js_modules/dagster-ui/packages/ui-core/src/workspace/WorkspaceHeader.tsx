import {QueryResult} from '@apollo/client';
import {PageHeader, Box, Heading, Button, Icon, Tooltip, Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {QueryRefreshState} from '../app/QueryRefresh';
import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from '../nav/ReloadRepositoryLocationButton';

import {WorkspaceTabs} from './WorkspaceTabs';
import {repoAddressAsHumanString} from './repoAddressAsString';
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
            <Link to="/locations" style={{color: Colors.textDefault()}}>
              Deployment
            </Link>
          </Heading>
          <Heading>/</Heading>
          <Heading style={{color: Colors.textLight()}}>
            {repoAddressAsHumanString(repoAddress)}
          </Heading>
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
        <ReloadRepositoryLocationButton
          location={repoAddress.location}
          ChildComponent={({tryReload, reloading, hasReloadPermission}) => {
            return (
              <Tooltip
                canShow={!hasReloadPermission}
                content={hasReloadPermission ? '' : NO_RELOAD_PERMISSION_TEXT}
                useDisabledButtonTooltipFix
              >
                <Button
                  onClick={() => tryReload()}
                  loading={reloading}
                  disabled={!hasReloadPermission}
                  icon={<Icon name="refresh" />}
                  outlined
                >
                  Reload definitions
                </Button>
              </Tooltip>
            );
          }}
        />
      }
    />
  );
};
