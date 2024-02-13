import {InMemoryCache} from '@apollo/client';

import possibleTypes from '../graphql/possibleTypes.generated.json';

export const createAppCache = () =>
  new InMemoryCache({
    possibleTypes,
    typePolicies: {
      PartitionStatus: {
        keyFields: false,
      },
    },
  });
