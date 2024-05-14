import {gql, useQuery} from '@apollo/client';

import {
  InstanceSupportsCapturedLogsQuery,
  InstanceSupportsCapturedLogsQueryVariables,
} from './types/useSupportsCapturedLogs.types';
import {useBlockTraceOnQueryResult} from '../performance/TraceContext';

export const useSupportsCapturedLogs = () => {
  const queryResult = useQuery<
    InstanceSupportsCapturedLogsQuery,
    InstanceSupportsCapturedLogsQueryVariables
  >(INSTANCE_SUPPORTS_CAPTURED_LOGS);
  useBlockTraceOnQueryResult(queryResult, 'InstanceSupportsCapturedLogsQuery');
  return !!queryResult.data?.instance.hasCapturedLogManager;
};

const INSTANCE_SUPPORTS_CAPTURED_LOGS = gql`
  query InstanceSupportsCapturedLogs {
    instance {
      id
      hasCapturedLogManager
    }
  }
`;
