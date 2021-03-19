import {ApolloClient, ApolloProvider} from '@apollo/client';
import {SchemaLink} from '@apollo/client/link/schema';
import {mergeResolvers} from '@graphql-tools/merge';
import {addMocksToSchema} from '@graphql-tools/mock';
import {makeExecutableSchema} from '@graphql-tools/schema';
import {loader} from 'graphql.macro';
import * as React from 'react';

import {AppCache} from '../app/AppCache';

import {defaultMocks} from './defaultMocks';

interface Props {
  children: React.ReactNode;
  mocks?: any;
}

const typeDefs = loader('../graphql/schema.graphql');
const schema = makeExecutableSchema({typeDefs});

export const ApolloTestProvider = (props: Props) => {
  const {children, mocks} = props;

  const client = React.useMemo(() => {
    const withMerge = mergeResolvers([defaultMocks, mocks]);
    const withMocks = addMocksToSchema({schema, mocks: withMerge});
    return new ApolloClient({
      cache: AppCache,
      link: new SchemaLink({schema: withMocks}),
    });
  }, [mocks]);

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
};
