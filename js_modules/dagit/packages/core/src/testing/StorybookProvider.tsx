import {loader} from 'graphql.macro';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';

import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';

const typeDefs = loader('../graphql/schema.graphql');

interface Props {
  routerProps?: MemoryRouterProps;
  apolloProps?: ApolloTestProps;
}

export const StorybookProvider: React.FC<Props> = (props) => {
  const {apolloProps, routerProps} = props;

  return (
    <MemoryRouter {...routerProps}>
      <ApolloTestProvider {...apolloProps} typeDefs={typeDefs}>
        <WorkspaceProvider>{props.children}</WorkspaceProvider>
      </ApolloTestProvider>
    </MemoryRouter>
  );
};
