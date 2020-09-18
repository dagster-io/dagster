import {
  InMemoryCache,
  IntrospectionFragmentMatcher,
  defaultDataIdFromObject,
} from 'apollo-cache-inmemory';

// this is a require cause otherwise it breaks
// eslint-disable-next-line @typescript-eslint/no-var-requires
const {__schema} = require('./filteredSchema.generated.json');

const fragmentMatcher = new IntrospectionFragmentMatcher({
  introspectionQueryResultData: {
    __schema,
  },
});

const AppCache = new InMemoryCache({
  addTypename: true,
  fragmentMatcher,
  cacheRedirects: {
    Query: {
      pipeline: (_, args, {getCacheKey}) => {
        return getCacheKey({__typename: 'Pipeline', name: args.name});
      },
      type: (_, args) => {
        // That's "IdValue" from 'apollo-utilities'.
        // Magical thing to make it work with interfaces, getCacheKey gets
        // incorrect typename and breaks
        return {
          type: 'id',
          generated: true,
          id: `Type.${args.typeName}`,
        };
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
    } else {
      return defaultDataIdFromObject(object);
    }
  },
});

export default AppCache;
