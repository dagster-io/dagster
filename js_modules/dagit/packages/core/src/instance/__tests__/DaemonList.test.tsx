import {MockedProvider} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import {buildDaemonStatus} from '../../graphql/types';
import {
  DaemonList,
  AUTOMATERIALIZE_PAUSED_QUERY,
  SET_AUTOMATERIALIZE_PAUSED_MUTATION,
} from '../DaemonList';

let mockResolveConfirmation = (_any: any) => {};
beforeEach(() => {
  mockResolveConfirmation = (_any: any) => {
    throw new Error('No confirmation mock defined');
  };
});

jest.mock('../../app/CustomConfirmationProvider', () => ({
  useConfirmation: () => {
    return async () => {
      await new Promise((resolve) => {
        mockResolveConfirmation = resolve;
      });
    };
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

const mocks = [
  {
    request: {
      query: AUTOMATERIALIZE_PAUSED_QUERY,
    },
    result: {
      data: {
        instance: {
          autoMaterializePaused: false,
        },
      },
    },
  },
];

describe('DaemonList', () => {
  it('renders daemons correctly', async () => {
    const {findByText, queryByText} = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <DaemonList daemonStatuses={mockDaemons} />
      </MockedProvider>,
    );

    expect(await findByText('Scheduler')).toBeInTheDocument();
    expect(await findByText('Sensors')).toBeInTheDocument();
    expect(await findByText('Auto-materializing')).toBeInTheDocument();

    // Check for non-existent daemon type
    expect(queryByText('NonExistentDaemon')).not.toBeInTheDocument();
  });

  it('toggles Auto-materializing correctly', async () => {
    const setAutoMaterializePausedMock = {
      request: {
        query: SET_AUTOMATERIALIZE_PAUSED_MUTATION,
        variables: {paused: true},
      },
      result: jest.fn(() => {
        return {data: {setAutoMaterializePaused: true}};
      }),
    };

    const {findByRole} = render(
      <MockedProvider mocks={[...mocks, setAutoMaterializePausedMock]} addTypename={false}>
        <DaemonList daemonStatuses={mockDaemons as any} />
      </MockedProvider>,
    );

    const switchButton = await findByRole('checkbox');
    userEvent.click(switchButton);
    // Confirmation required
    mockResolveConfirmation(0);
    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
    expect(switchButton).not.toBeChecked();
    userEvent.click(switchButton);
    // No confirmation this time.
    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
  });
});
