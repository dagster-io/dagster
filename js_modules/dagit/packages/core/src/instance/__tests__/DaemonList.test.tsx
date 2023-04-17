import {MockedProvider} from '@apollo/client/testing';
import {render, fireEvent, waitFor} from '@testing-library/react';
import React from 'react';

import {
  DaemonList,
  AUTOMATERIALIZE_PAUSED_QUERY,
  SET_AUTOMATERIALIZE_PAUSED_MUTATION,
} from '../DaemonList';

let mockResolveConfirmation = (_any: any) => {};
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
  {
    id: '1',
    daemonType: 'SCHEDULER',
    required: true,
    healthy: true,
    lastHeartbeatErrors: [],
    lastHeartbeatTime: 1000,
  },
  {
    id: '2',
    daemonType: 'SENSOR',
    required: true,
    healthy: true,
    lastHeartbeatErrors: [],
    lastHeartbeatTime: 2000,
  },
  {
    id: '3',
    daemonType: 'ASSET',
    required: true,
    healthy: true,
    lastHeartbeatErrors: [],
    lastHeartbeatTime: 3000,
  },
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
        <DaemonList daemonStatuses={mockDaemons as any} />
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
    fireEvent.click(switchButton);
    mockResolveConfirmation(0);
    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
  });
});
