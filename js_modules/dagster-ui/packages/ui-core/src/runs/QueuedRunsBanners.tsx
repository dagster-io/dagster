import {gql, useQuery} from '@apollo/client';
import {Alert, Box} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Link} from 'react-router-dom';

import {
  QueueDaemonStatusQuery,
  QueueDaemonStatusQueryVariables,
} from './types/QueuedRunsBanners.types';
import {InstancePageContext} from '../instance/InstancePageContext';
import {useCanSeeConfig} from '../instance/useCanSeeConfig';

export const QueuedRunsBanners = () => {
  const canSeeConfig = useCanSeeConfig();

  return (
    <Box flex={{direction: 'column', gap: 8}} style={{minWidth: '100%'}} border="bottom">
      {canSeeConfig && (
        <Alert
          intent="info"
          title={<Link to="/config#run_coordinator">View queue configuration</Link>}
        />
      )}
      {canSeeConfig && <QueueDaemonAlert />}
    </Box>
  );
};

const QueueDaemonAlert = () => {
  const {data} = useQuery<QueueDaemonStatusQuery, QueueDaemonStatusQueryVariables>(
    QUEUE_DAEMON_STATUS_QUERY,
  );
  const {pageTitle} = useContext(InstancePageContext);
  const status = data?.instance.daemonHealth.daemonStatus;
  if (status?.required && !status?.healthy) {
    return (
      <Alert
        intent="warning"
        title="The queued run coordinator is not healthy."
        description={
          <div>
            View <Link to="/health">{pageTitle}</Link> for details.
          </div>
        }
      />
    );
  }
  return null;
};

const QUEUE_DAEMON_STATUS_QUERY = gql`
  query QueueDaemonStatusQuery {
    instance {
      id
      daemonHealth {
        id
        daemonStatus(daemonType: "QUEUED_RUN_COORDINATOR") {
          id
          daemonType
          healthy
          required
        }
      }
    }
  }
`;
