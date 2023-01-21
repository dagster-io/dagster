import {gql, useQuery} from '@apollo/client';

import {InstanceConfigHasInfoQuery} from './types/useCanSeeConfig.types';

export const useCanSeeConfig = () => {
  const {data} = useQuery<InstanceConfigHasInfoQuery>(INSTANCE_CONFIG_HAS_INFO);
  return !!data?.instance.hasInfo;
};

const INSTANCE_CONFIG_HAS_INFO = gql`
  query InstanceConfigHasInfo {
    instance {
      hasInfo
    }
  }
`;
