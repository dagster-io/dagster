import {gql, useQuery} from '@apollo/client';
import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {InstanceWarningQuery} from 'src/nav/types/InstanceWarningQuery';
import {Group} from 'src/ui/Group';
import {WorkspaceContext} from 'src/workspace/WorkspaceContext';

export const InstanceWarningIcon = React.memo(() => {
  const {locations} = React.useContext(WorkspaceContext);

  const {data: healthData} = useQuery<InstanceWarningQuery>(INSTANCE_WARNING_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
  });

  const repoErrors = locations.filter(
    (node) => node.__typename === 'RepositoryLocationLoadFailure',
  );
  const daemonErrors =
    healthData?.instance.daemonHealth.allDaemonStatuses.filter(
      (daemon) => !daemon.healthy && daemon.required,
    ) || [];

  if (repoErrors.length || daemonErrors.length) {
    const content = (
      <Group direction="column" spacing={4}>
        {repoErrors.length ? (
          <div>{`${repoErrors.length} ${
            repoErrors.length === 1
              ? 'repository location failed to load'
              : 'repository locations failed to load'
          }`}</div>
        ) : null}
        {daemonErrors.length ? (
          <div>{`${daemonErrors.length} ${
            daemonErrors.length === 1 ? 'daemon not running' : 'daemons not running'
          }`}</div>
        ) : null}
      </Group>
    );
    return (
      <WarningTooltip content={content} position="right">
        <Icon icon="warning-sign" iconSize={12} color={Colors.GOLD3} title="Warnings found" />
      </WarningTooltip>
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

const WarningTooltip = styled(Tooltip)`
  display: block;

  .bp3-popover-target,
  .bp3-icon {
    display: block;
  }
`;
