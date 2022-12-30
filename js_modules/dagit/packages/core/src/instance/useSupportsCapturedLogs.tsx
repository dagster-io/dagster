import {gql, useQuery} from '@apollo/client';

import {InstanceSupportsCapturedLogs} from './types/InstanceSupportsCapturedLogs';

export const useSupportsCapturedLogs = () => {
  const {data} = useQuery<InstanceSupportsCapturedLogs>(INSTANCE_SUPPORTS_CAPTURED_LOGS);
  return !!data?.instance.hasCapturedLogManager;
};

const INSTANCE_SUPPORTS_CAPTURED_LOGS = gql`
  query InstanceSupportsCapturedLogs {
    instance {
      hasCapturedLogManager
    }
  }
`;
