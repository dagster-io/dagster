import {InMemoryCache, defaultDataIdFromObject} from '@apollo/client';

// this is a require cause otherwise it breaks
import possibleTypes from '../graphql/possibleTypes.generated.json';

export const createAppCache = () =>
  new InMemoryCache({
    addTypename: true,
    possibleTypes,
    dataIdFromObject: (object: any) => {
      if (
        object.name &&
        (object.__typename === 'RegularType' || object.__typename === 'CompositeType')
      ) {
        return `Type.${object.name}`;
      } else if (object.__typename === 'Instance') {
        return 'Instance';
      } else if (object.__typename === 'Workspace') {
        return 'Workspace';
      } else {
        return defaultDataIdFromObject(object);
      }
    },
  });
