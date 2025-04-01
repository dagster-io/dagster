import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {ReexecutionStrategy} from '../../graphql/types';
import {ReexecutionDialog} from '../ReexecutionDialog';
import {
  buildLaunchPipelineReexecutionErrorMock,
  buildLaunchPipelineReexecutionSuccessMock,
} from '../__fixtures__/Reexecution.fixtures';

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
          selectedRunBackfillIds={[]}
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

  it('allows you to specify one or more extra tags which are sent in the re-execute mutation', async () => {
    render(
      <Test
        strategy={ReexecutionStrategy.FROM_FAILURE}
        mocks={Object.keys(selectedMap).map((parentRunId) =>
          buildLaunchPipelineReexecutionSuccessMock({
            parentRunId,
            extraTags: [{key: 'test_key', value: 'test_value'}],
          }),
        )}
      />,
    );

    await userEvent.click(await screen.findByText('Add custom tag'));
    await userEvent.type(await screen.findByPlaceholderText('Tag Key'), 'test_key');
    await userEvent.type(await screen.findByPlaceholderText('Tag Value'), 'test_value');

    await waitFor(async () => {
      const button = screen.getByText(/re\-execute 3 runs/i);
      await userEvent.click(button);
    });

    await waitFor(() => {
      expect(screen.getByText(/Successfully requested re-execution for 3 runs./i)).toBeVisible();
    });
  });

  it('moves into loading state upon re-execution', async () => {
    render(
      <Test
        strategy={ReexecutionStrategy.FROM_FAILURE}
        mocks={Object.keys(selectedMap).map((parentRunId) =>
          buildLaunchPipelineReexecutionSuccessMock({parentRunId}),
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
          buildLaunchPipelineReexecutionSuccessMock({parentRunId}),
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
          buildLaunchPipelineReexecutionErrorMock({parentRunId: 'abcd-1234'}),
          buildLaunchPipelineReexecutionSuccessMock({parentRunId: 'efgh-5678'}),
          buildLaunchPipelineReexecutionErrorMock({parentRunId: 'ijkl-9012'}),
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
