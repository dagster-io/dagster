import * as React from 'react';
import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';

import {
  TerminateRunPolicy,
  TerminateRunsResultOrError,
  buildPythonError,
  buildRun,
  buildTerminateRunFailure,
  buildTerminateRunSuccess,
  buildTerminateRunsResult,
} from '../../graphql/types';
import {TERMINATE_MUTATION} from '../RunUtils';
import {TerminationDialog, Props as TerminationDialogProps} from '../TerminationDialog';
import {TerminateMutation, TerminateMutationVariables} from '../types/RunUtils.types';

// isOpen: boolean;
// onClose: () => void;

// // Fired when terimation has finished. You may want to refresh data in the parent
// // view but keep the dialog open so the user can view the results of termination.
// onComplete: (result: TerminationDialogResult) => void;

// // A map from the run ID to its `canTerminate` value
// selectedRuns: {[id: string]: boolean};
// selectedRunsAllQueued?: boolean;

function buildMockTerminateMutation(
  runIds: string[],
  terminatePolicy: TerminateRunPolicy,
  result?: TerminateRunsResultOrError,
): Omit<MockedResponse<TerminateMutation, TerminateMutationVariables>, 'result'> & {
  result: jest.Mock;
} {
  return {
    request: {
      query: TERMINATE_MUTATION,
      variables: {runIds, terminatePolicy},
    },
    result: jest.fn(() => ({
      data: {
        __typename: 'Mutation',
        terminateRuns:
          result ||
          buildTerminateRunsResult({
            terminateRunResults: [
              buildTerminateRunSuccess({run: buildRun({id: 'run-id-1'})}),
              buildTerminateRunFailure({
                run: buildRun({id: 'run-id-2'}),
                message: 'This is the error',
              }),
            ],
          }),
      },
    })),
  };
}

describe('TerminationDialog', () => {
  const Test = ({
    mocks,
    propOverrides,
  }: {
    mocks?: any;
    propOverrides?: Partial<TerminationDialogProps>;
  }) => {
    const props = {
      isOpen: true,
      onClose: () => {},
      onComplete: () => {},
      selectedRuns: {},
      ...propOverrides,
    };
    return (
      <MemoryRouter>
        <MockedProvider mocks={mocks}>
          <TerminationDialog {...props} />
        </MockedProvider>
      </MemoryRouter>
    );
  };

  it('shows the option to force termination if any canTerminate is true', async () => {
    render(<Test propOverrides={{selectedRuns: {'run-id-1': false, 'run-id-2': false}}} />);

    expect(screen.queryByTestId('force-termination-checkbox')).toBeNull();

    render(<Test propOverrides={{selectedRuns: {'run-id-1': true, 'run-id-2': false}}} />);

    expect(screen.queryByTestId('force-termination-checkbox')).not.toBeNull();
  });

  it('calls the terminate mutation with the SAFE_TERMINATE policy by default', async () => {
    const terminateMock = buildMockTerminateMutation(
      ['run-id-1', 'run-id-2'],
      TerminateRunPolicy.SAFE_TERMINATE,
    );
    render(
      <Test
        mocks={[terminateMock]}
        propOverrides={{selectedRuns: {'run-id-1': true, 'run-id-2': true}}}
      />,
    );

    await screen.getByTestId('terminate-button').click();
    await waitFor(() => expect(terminateMock.result).toHaveBeenCalled());
  });

  it('calls the terminate mutation with the MARK_AS_CANCELED_IMMEDIATELY policy if you check the "Force" checkbox', async () => {
    const terminateMock = buildMockTerminateMutation(
      ['run-id-1', 'run-id-2'],
      TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY,
    );
    render(
      <Test
        mocks={[terminateMock]}
        propOverrides={{selectedRuns: {'run-id-1': true, 'run-id-2': true}}}
      />,
    );

    await screen.getByTestId('force-termination-checkbox').click();
    await screen.getByTestId('terminate-button').click();
    await waitFor(() => expect(terminateMock.result).toHaveBeenCalled());
  });

  it('calls the terminate mutation with 75 IDs at a time for a large set of runs', async () => {
    const runIds = new Array(125).fill(0).map((_, idx) => `run-id-${idx}`);
    const terminateMock1 = buildMockTerminateMutation(
      runIds.slice(0, 75),
      TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY,
    );
    const terminateMock2 = buildMockTerminateMutation(
      runIds.slice(75),
      TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY,
    );
    render(
      <Test
        mocks={[terminateMock1, terminateMock2]}
        propOverrides={{selectedRuns: Object.fromEntries(runIds.map((r) => [r, true]))}}
      />,
    );

    await screen.getByTestId('force-termination-checkbox').click();
    await screen.getByTestId('terminate-button').click();
    await waitFor(() => expect(terminateMock1.result).toHaveBeenCalled());
    await waitFor(() => expect(terminateMock2.result).toHaveBeenCalled());
  });

  it('presents a summary of success and error results', async () => {
    const terminateMock = buildMockTerminateMutation(
      ['run-id-1', 'run-id-2'],
      TerminateRunPolicy.SAFE_TERMINATE,
    );
    render(
      <Test
        mocks={[terminateMock]}
        propOverrides={{selectedRuns: {'run-id-1': true, 'run-id-2': true}}}
      />,
    );

    await screen.getByTestId('terminate-button').click();
    await waitFor(() => expect(terminateMock.result).toHaveBeenCalled());

    await waitFor(() => {
      expect(screen.getByText('Successfully requested termination for 1 run.')).toBeVisible();
      expect(screen.getByText('Could not request termination for 1 run:')).toBeVisible();
      expect(screen.getByText('run-id-2')).toBeVisible();
      expect(screen.getByText('This is the error')).toBeVisible();
    });
  });

  it('presents a generic error if the mutation fails with a PythonError', async () => {
    const terminateMock = buildMockTerminateMutation(
      ['run-id-1', 'run-id-2'],
      TerminateRunPolicy.SAFE_TERMINATE,
      buildPythonError({message: 'Oh no python error'}),
    );
    render(
      <Test
        mocks={[terminateMock]}
        propOverrides={{selectedRuns: {'run-id-1': true, 'run-id-2': true}}}
      />,
    );

    await screen.getByTestId('terminate-button').click();
    await waitFor(() => expect(terminateMock.result).toHaveBeenCalled());

    await waitFor(() => {
      expect(
        screen.getByText('Sorry, an error occurred and the runs could not be terminated.'),
      ).toBeVisible();
    });
  });

  describe('when selectedRunsAllQueued is passed', () => {
    it('does not show the force termination option', async () => {
      render(
        <Test
          propOverrides={{
            selectedRuns: {'run-id-1': true, 'run-id-2': true},
            selectedRunsAllQueued: true,
          }}
        />,
      );
      expect(screen.queryByTestId('force-termination-checkbox')).toBeNull();
    });

    it('calls the terminate mutation with the MARK_AS_CANCELED_IMMEDIATELY policy', async () => {
      const terminateMock = buildMockTerminateMutation(
        ['run-id-1', 'run-id-2'],
        TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY,
      );
      render(
        <Test
          mocks={[terminateMock]}
          propOverrides={{
            selectedRuns: {'run-id-1': true, 'run-id-2': true},
            selectedRunsAllQueued: true,
          }}
        />,
      );

      await screen.getByTestId('terminate-button').click();
      await waitFor(() => expect(terminateMock.result).toHaveBeenCalled());
    });
  });
});
