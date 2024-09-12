import {
  InstanceConfigHasInfoQuery,
  InstanceConfigHasInfoQueryVariables,
} from './types/useCanSeeConfig.types';
import {gql, useQuery} from '../apollo-client';

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
