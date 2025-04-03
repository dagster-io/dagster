import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';

import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import RunsFeedRoot from '../RunsFeedRoot';
import {RunsFeedRootMock} from '../__fixtures__/RunsFeedRoot.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedRoot',
  component: RunsFeedRoot,
} as Meta;

export const Example = () => {
  return (
    <MockedProvider mocks={[RunsFeedRootMock]}>
      <WorkspaceProvider>
        <RunsFeedRoot />
      </WorkspaceProvider>
    </MockedProvider>
  );
};
