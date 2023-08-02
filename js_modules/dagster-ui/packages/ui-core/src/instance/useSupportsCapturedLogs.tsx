import {gql, useQuery} from '@apollo/client';

import {
  InstanceSupportsCapturedLogsQuery,
  InstanceSupportsCapturedLogsQueryVariables,
} from './types/useSupportsCapturedLogs.types';

export const useSupportsCapturedLogs = () => {
  const {data} = useQuery<
    InstanceSupportsCapturedLogsQuery,
    InstanceSupportsCapturedLogsQueryVariables
  >(INSTANCE_SUPPORTS_CAPTURED_LOGS);
  return !!data?.instance.hasCapturedLogManager;
};

const INSTANCE_SUPPORTS_CAPTURED_LOGS = gql`
  query InstanceSupportsCapturedLogs {
    instance {
      id
      hasCapturedLogManager
    }
  }
`;
