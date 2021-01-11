import {gql, useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {InstanceWarningQuery} from 'src/nav/types/InstanceWarningQuery';
import {WorkspaceContext} from 'src/workspace/WorkspaceContext';

export const InstanceWarningIcon = React.memo(() => {
  const {locations} = React.useContext(WorkspaceContext);

  const {data: healthData} = useQuery<InstanceWarningQuery>(INSTANCE_WARNING_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
  });

  const repoErrors = locations.some((node) => node.__typename === 'RepositoryLocationLoadFailure');
  const daemonErrors = healthData?.instance.daemonHealth.allDaemonStatuses.some(
    (daemon) => !daemon.healthy && daemon.required,
  );

  if (repoErrors || daemonErrors) {
    return (
      <WarningIcon icon="warning-sign" iconSize={12} color={Colors.GOLD3} title="Warnings found" />
    );
  }

  return null;
});

const INSTANCE_WARNING_QUERY = gql`
  query InstanceWarningQuery {
    instance {
      ...InstanceHealthFragment
    }
  }
  ${INSTANCE_HEALTH_FRAGMENT}
`;

const WarningIcon = styled(Icon)`
  display: block;
`;
