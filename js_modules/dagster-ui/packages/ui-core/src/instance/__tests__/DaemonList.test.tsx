import {MockedResponse, MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import {CustomConfirmationProvider} from '../../app/CustomConfirmationProvider';
import {
  AUTOMATERIALIZE_PAUSED_QUERY,
  SET_AUTOMATERIALIZE_PAUSED_MUTATION,
} from '../../assets/AutomaterializeDaemonStatusTag';
import {GetAutoMaterializePausedQuery} from '../../assets/types/AutomaterializeDaemonStatusTag.types';
import {buildDaemonStatus, buildInstance} from '../../graphql/types';
import {DaemonList} from '../DaemonList';

jest.mock('../../app/Permissions', () => ({
  useUnscopedPermissions: () => {
    return {permissions: {canToggleAutoMaterialize: true}};
  },
}));

const mockDaemons = [
  buildDaemonStatus({
    id: '1',
    daemonType: 'SCHEDULER',
    required: true,
    healthy: true,
    lastHeartbeatErrors: [],
    lastHeartbeatTime: 1000,
  }),
  buildDaemonStatus({
    id: '2',
    daemonType: 'SENSOR',
    required: true,
    healthy: true,
    lastHeartbeatErrors: [],
    lastHeartbeatTime: 2000,
  }),
  buildDaemonStatus({
    id: '3',
    daemonType: 'ASSET',
    required: true,
    healthy: true,
    lastHeartbeatErrors: [],
    lastHeartbeatTime: 3000,
  }),
];

function autoMaterializePausedMock(paused: boolean): MockedResponse<GetAutoMaterializePausedQuery> {
  return {
    request: {
      query: AUTOMATERIALIZE_PAUSED_QUERY,
    },
    result: jest.fn(() => {
      return {
        data: {
          __typename: 'Query',
          instance: buildInstance({
            autoMaterializePaused: paused,
          }),
        },
      };
    }),
  };
}

describe('DaemonList', () => {
  it('renders daemons correctly', async () => {
    const {findByText, queryByText} = render(
      <MockedProvider mocks={[autoMaterializePausedMock(false)]}>
        <DaemonList daemonStatuses={mockDaemons} />
      </MockedProvider>,
    );

    expect(await findByText('Scheduler')).toBeInTheDocument();
    expect(await findByText('Sensors')).toBeInTheDocument();
    expect(await findByText('Auto-materializing')).toBeInTheDocument();

    // Check for non-existent daemon type
    expect(queryByText('NonExistentDaemon')).not.toBeInTheDocument();
  });

  it('turns off Auto-materializing', async () => {
    const setAutoMaterializePausedMock = {
      request: {
        query: SET_AUTOMATERIALIZE_PAUSED_MUTATION,
        variables: {paused: true},
      },
      result: jest.fn(() => {
        return {data: {setAutoMaterializePaused: true}};
      }),
    };

    render(
      <MockedProvider mocks={[autoMaterializePausedMock(false), setAutoMaterializePausedMock]}>
        <CustomConfirmationProvider>
          <DaemonList daemonStatuses={mockDaemons} />
        </CustomConfirmationProvider>
      </MockedProvider>,
    );

    const switchButton = await screen.findByRole('checkbox');
    expect(switchButton).toBeChecked();
    expect(switchButton).toBeEnabled();

    await userEvent.click(switchButton);
    expect(setAutoMaterializePausedMock.result).not.toHaveBeenCalled();

    const confirmButton = await screen.findByRole('button', {name: /confirm/i});
    await userEvent.click(confirmButton);

    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
  });

  it('turns on Auto-materializing', async () => {
    const setAutoMaterializePausedMock = {
      request: {
        query: SET_AUTOMATERIALIZE_PAUSED_MUTATION,
        variables: {paused: false},
      },
      result: jest.fn(() => {
        return {data: {setAutoMaterializePaused: true}};
      }),
    };

    render(
      <MockedProvider mocks={[autoMaterializePausedMock(true), setAutoMaterializePausedMock]}>
        <CustomConfirmationProvider>
          <DaemonList daemonStatuses={mockDaemons} />
        </CustomConfirmationProvider>
      </MockedProvider>,
    );

    const switchButton = await screen.findByRole('checkbox');
    expect(switchButton).not.toBeChecked();
    expect(switchButton).toBeEnabled();

    await userEvent.click(switchButton);
    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
  });
});
