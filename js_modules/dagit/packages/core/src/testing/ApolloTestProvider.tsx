import {ApolloClient, ApolloProvider, DocumentNode} from '@apollo/client';
import {SchemaLink} from '@apollo/client/link/schema';
import {mergeResolvers} from '@graphql-tools/merge';
import {addMocksToSchema} from '@graphql-tools/mock';
import {makeExecutableSchema} from '@graphql-tools/schema';
import * as React from 'react';

import {AppCache} from '../app/AppCache';

import {defaultMocks} from './defaultMocks';

export interface ApolloTestProps {
  mocks?: any;
}

interface Props extends ApolloTestProps {
  typeDefs: DocumentNode;
}

export const ApolloTestProvider: React.FC<Props> = (props) => {
  const {children, mocks, typeDefs} = props;

  const client = React.useMemo(() => {
    const withMerge = mergeResolvers([defaultMocks, mocks]);
    const schema = makeExecutableSchema({typeDefs});
    const withMocks = addMocksToSchema({schema, mocks: withMerge});
    return new ApolloClient({
      cache: AppCache,
      link: new SchemaLink({schema: withMocks}),
    });
  }, [mocks, typeDefs]);

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
};
