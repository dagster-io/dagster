import {useQuery} from '@apollo/client';

import {graphql} from '../graphql';

export const useSupportsCapturedLogs = () => {
  const {data} = useQuery(INSTANCE_SUPPORTS_CAPTURED_LOGS);
  return !!data?.instance.hasCapturedLogManager;
};

const INSTANCE_SUPPORTS_CAPTURED_LOGS = graphql(`
  query InstanceSupportsCapturedLogs {
    instance {
      hasCapturedLogManager
    }
  }
`);
