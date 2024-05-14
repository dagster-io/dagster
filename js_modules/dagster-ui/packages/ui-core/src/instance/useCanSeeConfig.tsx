import {gql, useQuery} from '@apollo/client';

import {
  InstanceConfigHasInfoQuery,
  InstanceConfigHasInfoQueryVariables,
} from './types/useCanSeeConfig.types';
import {useBlockTraceOnQueryResult} from '../performance/TraceContext';

export const useCanSeeConfig = () => {
  const queryResult = useQuery<InstanceConfigHasInfoQuery, InstanceConfigHasInfoQueryVariables>(
    INSTANCE_CONFIG_HAS_INFO,
  );
  useBlockTraceOnQueryResult(queryResult, 'InstanceConfigHasInfoQuery');
  return !!queryResult.data?.instance.hasInfo;
};

const INSTANCE_CONFIG_HAS_INFO = gql`
  query InstanceConfigHasInfo {
    instance {
      id
      hasInfo
    }
  }
`;
