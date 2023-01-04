import {graphql} from '../graphql';

export const INSTANCE_HEALTH_FRAGMENT = graphql(`
  fragment InstanceHealthFragment on Instance {
    daemonHealth {
      id
      ...DaemonHealthFragment
    }
    hasInfo
  }
`);
