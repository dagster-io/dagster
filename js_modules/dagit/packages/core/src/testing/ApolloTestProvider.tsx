import {ApolloClient, ApolloProvider, DocumentNode} from '@apollo/client';
import {SchemaLink} from '@apollo/client/link/schema';
import {mergeResolvers} from '@graphql-tools/merge';
import {addMocksToSchema} from '@graphql-tools/mock';
import {makeExecutableSchema} from '@graphql-tools/schema';
import * as React from 'react';

import {createAppCache} from '../app/AppCache';

import {defaultMocks} from './defaultMocks';

export interface ApolloTestProps {
  /**
   * Either a resolver object or an array of resolver objects.
   *
   * If you have test-level default mocks that may be overridden on a per-test basis,
   * pass an array of the mock resolver objects:
   *
   * <ApolloTestProvider mocks={[defaultMocks, mocks]}>
   *
   * Within `ApolloTestProvider`, `mergeResolvers` will handle merging the mock resolve
   * objects.
   */
  mocks?: any;
}

interface Props extends ApolloTestProps {
  typeDefs: DocumentNode;
}

export const ApolloTestProvider: React.FC<Props> = (props) => {
  const {children, mocks = [], typeDefs} = props;

  const client = React.useMemo(() => {
    const toMerge = Array.isArray(mocks) ? mocks : [mocks];
    const withMerge = mergeResolvers([defaultMocks, ...toMerge]);
    const schema = makeExecutableSchema({typeDefs});
    const withMocks = addMocksToSchema({schema, mocks: withMerge});
    const cache = createAppCache();
    return new ApolloClient({
      cache,
      link: new SchemaLink({schema: withMocks}),
    });
  }, [mocks, typeDefs]);

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
};
