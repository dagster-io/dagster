import {ApolloClient, ApolloProvider} from '@apollo/client';
import {SchemaLink} from '@apollo/client/link/schema';
import {mergeResolvers} from '@graphql-tools/merge';
import {addMocksToSchema} from '@graphql-tools/mock';
import {makeExecutableSchema} from '@graphql-tools/schema';
import {loader} from 'graphql.macro';
import * as React from 'react';

import {AppCache} from 'src/AppCache';
import {defaultMocks} from 'src/testing/defaultMocks';

interface Props {
  children: React.ReactNode;
  mocks?: any;
}

export const ApolloTestProvider = (props: Props) => {
  const {children, mocks} = props;

  const client = React.useMemo(() => {
    // The loader has to live here instead of the module level, otherwise we can end
    // up with nondeterministic behavior when querying/caching.
    const schemaDefinition = loader('../schema.graphql');

    const schema = makeExecutableSchema({typeDefs: schemaDefinition});
    const withMerge = mergeResolvers([defaultMocks, mocks]);
    const withMocks = addMocksToSchema({schema, mocks: withMerge});
    return new ApolloClient({
      cache: AppCache,
      link: new SchemaLink({schema: withMocks}),
    });
  }, [mocks]);

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
};
