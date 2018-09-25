import {
  InMemoryCache,
  IntrospectionFragmentMatcher,
  defaultDataIdFromObject
} from "apollo-cache-inmemory";
// this is a require cause otherwise it breaks
const introspectionQueryResultData = require("./schema.json");

const fragmentMatcher = new IntrospectionFragmentMatcher({
  introspectionQueryResultData: {
    __schema: introspectionQueryResultData
  }
});

const AppCache = new InMemoryCache({
  fragmentMatcher,
  cacheRedirects: {
    Query: {
      pipeline: (_, args, { getCacheKey }) =>
        getCacheKey({ __typename: "Pipeline", name: args.name })
    }
  },
  dataIdFromObject: (object: any) => {
    if (object.__typename === "Pipeline" && object.name) {
      return `Pipeline.${object.name}`;
    } else {
      return defaultDataIdFromObject(object);
    }
  }
});

export default AppCache;
