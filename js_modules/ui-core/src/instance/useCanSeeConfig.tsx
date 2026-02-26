import {gql, useQuery} from '../apollo-client';
import {
  InstanceConfigHasInfoQuery,
  InstanceConfigHasInfoQueryVariables,
} from './types/useCanSeeConfig.types';

export const useCanSeeConfig = () => {
  const queryResult = useQuery<InstanceConfigHasInfoQuery, InstanceConfigHasInfoQueryVariables>(
    INSTANCE_CONFIG_HAS_INFO,
  );
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
