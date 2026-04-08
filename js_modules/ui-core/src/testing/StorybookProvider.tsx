import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {CustomAlertProvider} from '../app/CustomAlertProvider';
import {WorkspaceProvider} from '../workspace/WorkspaceContext/WorkspaceContext';

interface Props {
  children: React.ReactNode;
  routerProps?: MemoryRouterProps;
  mocks?: MockedResponse[];
}

export const StorybookProvider = (props: Props) => {
  const {mocks = [], routerProps} = props;

  return (
    <RecoilRoot>
      <MemoryRouter {...routerProps}>
        <MockedProvider mocks={mocks}>
          <CustomAlertProvider />
          <WorkspaceProvider>{props.children}</WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>
    </RecoilRoot>
  );
};
