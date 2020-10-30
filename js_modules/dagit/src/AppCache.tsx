import {InMemoryCache, defaultDataIdFromObject} from '@apollo/client';

// this is a require cause otherwise it breaks
// eslint-disable-next-line @typescript-eslint/no-var-requires
const possibleTypes = require('./possibleTypes.generated.json');

export const AppCache = new InMemoryCache({
  addTypename: true,
  possibleTypes,
  typePolicies: {
    Query: {
      fields: {
        pipeline: (_, {args, toReference}) => {
          return toReference({__typename: 'Pipeline', name: args?.name});
        },
        type: (_, {args}) => {
          // That's "IdValue" from '@apollo/client/utilities'.
          // Magical thing to make it work with interfaces, getCacheKey gets
          // incorrect typename and breaks
          return {
            type: 'id',
            generated: true,
            id: `Type.${args?.typeName}`,
          };
        },
      },
    },
  },
  dataIdFromObject: (object: any) => {
    if (object.name && object.__typename === 'Pipeline') {
      return `${object.__typename}.${object.name}`;
    } else if (object.runId && object.__typename === 'PipelineRun') {
      return `${object.__typename}.${object.runId}`;
    } else if (
      object.name &&
      (object.__typename === 'RegularType' || object.__typename === 'CompositeType')
    ) {
      return `Type.${object.name}`;
    } else if (object.__typename === 'Instance') {
      return 'Instance';
    } else if (object.__typename === 'RepositoryLocation') {
      return `RepositoryLocation:${object.name}`;
    } else {
      return defaultDataIdFromObject(object);
    }
  },
});
