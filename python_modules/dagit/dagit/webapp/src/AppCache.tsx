import {
  InMemoryCache,
  IntrospectionFragmentMatcher
} from "apollo-cache-inmemory";
// this is a require cause otherwise it breaks
const introspectionQueryResultData = require("./schema.json");

const fragmentMatcher = new IntrospectionFragmentMatcher({
  introspectionQueryResultData: {
    __schema: introspectionQueryResultData
  }
});

const AppCache = new InMemoryCache({ fragmentMatcher });

export default AppCache;
