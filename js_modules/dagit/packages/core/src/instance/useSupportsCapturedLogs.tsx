import {gql, useQuery} from '@apollo/client';

import {InstanceSupportsCapturedLogsQuery} from './types/useSupportsCapturedLogs.types';

export const useSupportsCapturedLogs = () => {
  const {data} = useQuery<InstanceSupportsCapturedLogsQuery>(INSTANCE_SUPPORTS_CAPTURED_LOGS);
  return !!data?.instance.hasCapturedLogManager;
};

const INSTANCE_SUPPORTS_CAPTURED_LOGS = gql`
  query InstanceSupportsCapturedLogs {
    instance {
      hasCapturedLogManager
    }
  }
`;
