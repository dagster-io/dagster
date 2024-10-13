import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';

import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import RunsRoot from '../RunsRoot';
import {RunsRootMock} from '../__fixtures__/RunsRoot.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsRoot',
  component: RunsRoot,
} as Meta;

export const Example = () => {
  return (
    // // Repeat mock multiple times since the query is refreshed
    <MockedProvider
      mocks={[RunsRootMock, RunsRootMock, RunsRootMock, RunsRootMock, RunsRootMock, RunsRootMock]}
    >
      <WorkspaceProvider>
        <RunsRoot />
      </WorkspaceProvider>
    </MockedProvider>
  );
};
