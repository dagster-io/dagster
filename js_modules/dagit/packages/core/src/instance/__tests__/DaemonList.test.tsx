import {MockedResponse, MockedProvider} from '@apollo/client/testing';
import {fireEvent, render, waitFor} from '@testing-library/react';
import React from 'react';

import {
  AUTOMATERIALIZE_PAUSED_QUERY,
  SET_AUTOMATERIALIZE_PAUSED_MUTATION,
} from '../../assets/AutomaterializeDaemonStatusTag';
import {GetAutoMaterializePausedQuery} from '../../assets/types/AutomaterializeDaemonStatusTag.types';
import {buildDaemonStatus, buildInstance} from '../../graphql/types';
import {DaemonList} from '../DaemonList';

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

function autoMaterializePausedMock(paused: boolean): MockedResponse<GetAutoMaterializePausedQuery> {
  return {
    request: {
      query: AUTOMATERIALIZE_PAUSED_QUERY,
    },
    result: jest.fn(() => {
      return {
        data: {
          __typename: 'DagitQuery',
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

    const {findByRole} = render(
      <MockedProvider mocks={[autoMaterializePausedMock(false), setAutoMaterializePausedMock]}>
        <DaemonList daemonStatuses={mockDaemons} />
      </MockedProvider>,
    );

    const switchButton = await findByRole('checkbox');
    expect(switchButton).toBeChecked();

    fireEvent.click(switchButton);

    await waitFor(() => expect(setAutoMaterializePausedMock.result).not.toHaveBeenCalled());

    await waitFor(() => {
      expect(() => {
        // Confirmation required
        mockResolveConfirmation(0);
      }).not.toThrow();
    });

    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
  });

  it('turns ob Auto-materializing', async () => {
    const setAutoMaterializePausedMock = {
      request: {
        query: SET_AUTOMATERIALIZE_PAUSED_MUTATION,
        variables: {paused: false},
      },
      result: jest.fn(() => {
        return {data: {setAutoMaterializePaused: true}};
      }),
    };

    const {findByRole} = render(
      <MockedProvider mocks={[autoMaterializePausedMock(true), setAutoMaterializePausedMock]}>
        <DaemonList daemonStatuses={mockDaemons} />
      </MockedProvider>,
    );

    const switchButton = await findByRole('checkbox');
    expect(switchButton).not.toBeChecked();

    fireEvent.click(switchButton);

    await waitFor(() => expect(setAutoMaterializePausedMock.result).not.toHaveBeenCalled());

    await waitFor(() => {
      expect(() => {
        // Confirmation required
        mockResolveConfirmation(0);
      }).toThrow();
    });

    await waitFor(() => expect(setAutoMaterializePausedMock.result).toHaveBeenCalled());
  });
});
