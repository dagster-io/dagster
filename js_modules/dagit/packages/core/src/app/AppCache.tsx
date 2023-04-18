import {InMemoryCache} from '@apollo/client';

import possibleTypes from '../graphql/possibleTypes.generated.json';

export const createAppCache = () =>
  new InMemoryCache({
    addTypename: true,
    possibleTypes,
    typePolicies: {
      PartitionStatus: {
        keyFields: false,
      },
    },
  });
