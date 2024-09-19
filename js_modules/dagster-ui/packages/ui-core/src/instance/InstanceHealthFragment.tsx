import {DAEMON_HEALTH_FRAGMENT} from './DaemonList';
import {gql} from '../apollo-client';

export const INSTANCE_HEALTH_FRAGMENT = gql`
  fragment InstanceHealthFragment on Instance {
    id
    daemonHealth {
      id
      ...DaemonHealthFragment
    }
    hasInfo
  }

  ${DAEMON_HEALTH_FRAGMENT}
`;
