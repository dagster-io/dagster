import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {POLL_INTERVAL} from '../runs/useCursorPaginatedQuery';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Subheading} from '../ui/Text';
import {REPOSITORY_LOCATIONS_FRAGMENT} from '../workspace/WorkspaceContext';

import {DaemonList} from './DaemonList';
import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstanceTabs} from './InstanceTabs';
import {InstanceHealthQuery} from './types/InstanceHealthQuery';

export const InstanceHealthPage = () => {
  const queryData = useQuery<InstanceHealthQuery>(INSTANCE_HEALTH_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    notifyOnNetworkStatusChange: true,
  });

  const {loading, data} = queryData;

  const daemonContent = () => {
    if (loading && !data?.instance) {
      return <div style={{color: Colors.GRAY3}}>Loading…</div>;
    }
    return data?.instance ? <DaemonList daemonHealth={data.instance.daemonHealth} /> : null;
  };

  return (
    <Group direction="column" spacing={20}>
      <InstanceTabs tab="health" queryData={queryData} />
      <Group direction="column" spacing={16}>
        <Box padding={{horizontal: 24}}>
          <Subheading>Daemon statuses</Subheading>
        </Box>
        {daemonContent()}
      </Group>
    </Group>
  );
};

const INSTANCE_HEALTH_QUERY = gql`
  query InstanceHealthQuery {
    instance {
      ...InstanceHealthFragment
    }
    workspaceOrError {
      ...RepositoryLocationsFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_LOCATIONS_FRAGMENT}
`;
