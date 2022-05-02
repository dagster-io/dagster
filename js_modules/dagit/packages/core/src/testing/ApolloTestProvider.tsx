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
   * Either a mock object or an array of mock objects.
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

  resolvers?: any;
}

interface Props extends ApolloTestProps {
  typeDefs: DocumentNode;
}

export const ApolloTestProvider: React.FC<Props> = (props) => {
  const {children, mocks = [], typeDefs, resolvers = []} = props;

  const client = React.useMemo(() => {
    const mocksToMerge = Array.isArray(mocks) ? mocks : [mocks];
    const mocksWithMerge = mergeResolvers([defaultMocks, ...mocksToMerge]);

    const schema = makeExecutableSchema({typeDefs});
    const mockedSchema = addMocksToSchema({
      schema,
      mocks: mocksWithMerge,
      resolvers: () => {
        return mergeResolvers(resolvers);
      },
    });
    const cache = createAppCache();
    return new ApolloClient({
      cache,
      link: new SchemaLink({schema: mockedSchema}),
    });
  }, [mocks, typeDefs, resolvers]);

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
};
