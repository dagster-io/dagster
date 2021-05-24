import {gql, useQuery} from '@apollo/client';
import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {Group} from '../ui/Group';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {InstanceWarningQuery} from './types/InstanceWarningQuery';

export const InstanceWarningIcon = React.memo(() => {
  const {locationEntries} = React.useContext(WorkspaceContext);

  const {data: healthData} = useQuery<InstanceWarningQuery>(INSTANCE_WARNING_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
  });

  const repoErrors = locationEntries.filter(
    (locationEntry) => locationEntry.locationOrLoadError?.__typename === 'PythonError',
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
        <Icon icon="warning-sign" iconSize={14} color={Colors.GOLD4} title="Warnings found" />
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
  outline: none;

  .bp3-popover-target,
  .bp3-icon {
    display: block;
  }

  .bp3-icon:focus,
  .bp3-icon:active {
    outline: none;
  }
`;
