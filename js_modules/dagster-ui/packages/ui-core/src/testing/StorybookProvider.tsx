import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';
import {CustomAlertProvider} from '../app/CustomAlertProvider';
import typeDefs from '../graphql/schema.graphql';
import {WorkspaceProvider} from '../workspace/WorkspaceContext/WorkspaceContext';

interface Props {
  children: React.ReactNode;
  routerProps?: MemoryRouterProps;
  apolloProps?: ApolloTestProps;
}

export const StorybookProvider = (props: Props) => {
  const {apolloProps, routerProps} = props;

  return (
    <RecoilRoot>
      <MemoryRouter {...routerProps}>
        <ApolloTestProvider {...apolloProps} typeDefs={typeDefs as any}>
          <CustomAlertProvider />
          <WorkspaceProvider>{props.children}</WorkspaceProvider>
        </ApolloTestProvider>
      </MemoryRouter>
    </RecoilRoot>
  );
};
