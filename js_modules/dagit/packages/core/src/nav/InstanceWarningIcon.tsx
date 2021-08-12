import {gql, useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';

import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';

import {WarningTooltip} from './WarningTooltip';
import {InstanceWarningQuery} from './types/InstanceWarningQuery';

export const InstanceWarningIcon = React.memo(() => {
  const {data: healthData} = useQuery<InstanceWarningQuery>(INSTANCE_WARNING_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
  });

  const daemonErrors =
    healthData?.instance.daemonHealth.allDaemonStatuses.filter(
      (daemon) => !daemon.healthy && daemon.required,
    ) || [];

  if (daemonErrors.length) {
    return (
      <WarningTooltip
        content={
          <div>{`${daemonErrors.length} ${
            daemonErrors.length === 1 ? 'daemon not running' : 'daemons not running'
          }`}</div>
        }
        position="right"
      >
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
