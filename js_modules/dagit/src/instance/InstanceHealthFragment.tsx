import {gql} from '@apollo/client';

import {DAEMON_HEALTH_FRAGMENT} from 'src/instance/DaemonList';

export const INSTANCE_HEALTH_FRAGMENT = gql`
  fragment InstanceHealthFragment on Instance {
    daemonHealth {
      id
      ...DaemonHealthFragment
    }
  }
  ${DAEMON_HEALTH_FRAGMENT}
`;
