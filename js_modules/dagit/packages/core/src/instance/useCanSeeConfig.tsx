import {gql, useQuery} from '@apollo/client';

import {InstanceConfigHasInfo} from './types/InstanceConfigHasInfo';

export const useCanSeeConfig = () => {
  const {data} = useQuery<InstanceConfigHasInfo>(INSTANCE_CONFIG_HAS_INFO);
  return !!data?.instance.hasInfo;
};

const INSTANCE_CONFIG_HAS_INFO = gql`
  query InstanceConfigHasInfo {
    instance {
      hasInfo
    }
  }
`;
