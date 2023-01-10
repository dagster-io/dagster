import {useQuery} from '@apollo/client';

import {graphql} from '../graphql';

export const useCanSeeConfig = () => {
  const {data} = useQuery(INSTANCE_CONFIG_HAS_INFO);
  return !!data?.instance.hasInfo;
};

const INSTANCE_CONFIG_HAS_INFO = graphql(`
  query InstanceConfigHasInfo {
    instance {
      hasInfo
    }
  }
`);
