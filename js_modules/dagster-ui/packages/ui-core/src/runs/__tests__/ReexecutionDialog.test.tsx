import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ReexecutionStrategy} from '../../graphql/types';
import {ReexecutionDialog} from '../ReexecutionDialog';
import {LAUNCH_PIPELINE_REEXECUTION_MUTATION} from '../RunUtils';
import {LaunchPipelineReexecutionMutation} from '../types/RunUtils.types';

const buildLaunchPipelineReexecutionSuccessMock = (
  parentRunId: string,
): MockedResponse<LaunchPipelineReexecutionMutation> => ({
  request: {
    query: LAUNCH_PIPELINE_REEXECUTION_MUTATION,
    variables: {reexecutionParams: {parentRunId, strategy: 'FROM_FAILURE'}},
  },
  result: {
    data: {
      __typename: 'Mutation',
      launchPipelineReexecution: {
        __typename: 'LaunchRunSuccess',
        run: {
          id: '1234',
          pipelineName: '1234',
          rootRunId: null,
          parentRunId,
          __typename: 'Run',
        },
      },
    },
  },
});

const buildLaunchPipelineReexecutionErrorMock = (
  parentRunId: string,
): MockedResponse<LaunchPipelineReexecutionMutation> => ({
  request: {
    query: LAUNCH_PIPELINE_REEXECUTION_MUTATION,
    variables: {reexecutionParams: {parentRunId, strategy: 'FROM_FAILURE'}},
  },
  result: {
    data: {
      __typename: 'Mutation',
      launchPipelineReexecution: {
        __typename: 'PythonError',
        errorChain: [],
        message: 'A wild python error appeared!',
        stack: [],
      },
    },
  },
});

describe('ReexecutionDialog', () => {
  const selectedMap = {
    'abcd-1234': 'abcd-1234',
    'efgh-5678': 'efgh-5678',
    'ijkl-9012': 'ijkl-9012',
  };

  const Test = (props: {strategy: ReexecutionStrategy; mocks?: MockedResponse[]}) => (
    <MockedProvider mocks={props.mocks}>
      <MemoryRouter>
        <ReexecutionDialog
          isOpen
          onClose={jest.fn()}
          onComplete={jest.fn()}
          selectedRuns={selectedMap}
          reexecutionStrategy={props.strategy}
        />
      </MemoryRouter>
    </MockedProvider>
  );

  it('prompts the user with the number of runs to re-execute', async () => {
    render(<Test strategy={ReexecutionStrategy.FROM_FAILURE} />);

    await waitFor(() => {
      const message = screen.getByText(/3 runs will be re\-executed \. do you wish to continue\?/i);
      expect(message).toBeVisible();
      expect(within(message).getByText(/from failure/i)).toBeVisible();
    });
  });

  it('moves into loading state upon re-execution', async () => {
    render(
      <Test
        strategy={ReexecutionStrategy.FROM_FAILURE}
        mocks={Object.keys(selectedMap).map((parentRunId) =>
          buildLaunchPipelineReexecutionSuccessMock(parentRunId),
        )}
      />,
    );

    await waitFor(() => {
      const message = screen.getByText(/3 runs will be re\-executed \. do you wish to continue\?/i);
      expect(message).toBeVisible();
      expect(within(message).getByText(/from failure/i)).toBeVisible();
    });

    const button = screen.getByText(/re\-execute 3 runs/i);
    await userEvent.click(button);

    await waitFor(() => {
      expect(
        screen.getByText(/Please do not close the window or navigate away during re-execution./i),
      ).toBeVisible();
      expect(screen.getByRole('button', {name: /Re-executing 3 runs.../i})).toBeVisible();
    });
  });

  it('displays success message if mutations are successful', async () => {
    render(
      <Test
        strategy={ReexecutionStrategy.FROM_FAILURE}
        mocks={Object.keys(selectedMap).map((parentRunId) =>
          buildLaunchPipelineReexecutionSuccessMock(parentRunId),
        )}
      />,
    );

    await waitFor(async () => {
      const button = screen.getByText(/re\-execute 3 runs/i);
      await userEvent.click(button);
    });

    await waitFor(() => {
      expect(screen.getByText(/Successfully requested re-execution for 3 runs./i)).toBeVisible();
    });
  });

  it('displays python errors', async () => {
    render(
      <Test
        strategy={ReexecutionStrategy.FROM_FAILURE}
        mocks={[
          buildLaunchPipelineReexecutionErrorMock('abcd-1234'),
          buildLaunchPipelineReexecutionSuccessMock('efgh-5678'),
          buildLaunchPipelineReexecutionErrorMock('ijkl-9012'),
        ]}
      />,
    );

    await waitFor(async () => {
      const button = screen.getByText(/re\-execute 3 runs/i);
      await userEvent.click(button);
    });

    await waitFor(() => {
      expect(screen.getByText(/Successfully requested re-execution for 1 run./i)).toBeVisible();
      expect(screen.getAllByText(/A wild python error appeared!/i)).toHaveLength(2);
    });
  });
});
