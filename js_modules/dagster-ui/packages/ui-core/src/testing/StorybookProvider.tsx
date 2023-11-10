import {loader} from 'graphql.macro';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';

import {CustomAlertProvider} from '../app/CustomAlertProvider';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';

const typeDefs = loader('../graphql/schema.graphql');

interface Props {
  children: React.ReactNode;
  routerProps?: MemoryRouterProps;
  apolloProps?: ApolloTestProps;
}

export const StorybookProvider = (props: Props) => {
  const {apolloProps, routerProps} = props;

  return (
    <MemoryRouter {...routerProps}>
      <ApolloTestProvider {...apolloProps} typeDefs={typeDefs as any}>
        <CustomAlertProvider />
        <WorkspaceProvider>{props.children}</WorkspaceProvider>
      </ApolloTestProvider>
    </MemoryRouter>
  );
};
