import {render, screen, waitFor, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {ReexecutionStrategy} from '../types/globalTypes';

import {ReexecutionDialog} from './ReexecutionDialog';

describe('ReexecutionDialog', () => {
  const selectedMap = {
    'abcd-1234': 'abcd-1234',
    'efgh-5678': 'efgh-5678',
    'ijkl-9012': 'ijkl-9012',
  };

  const Test = (props: {strategy: ReexecutionStrategy}) => (
    <ReexecutionDialog
      isOpen
      onClose={jest.fn()}
      onComplete={jest.fn()}
      selectedRuns={selectedMap}
      reexecutionStrategy={props.strategy}
    />
  );

  it('prompts the user with the number of runs to re-execute', async () => {
    render(
      <TestProvider>
        <Test strategy={ReexecutionStrategy.FROM_FAILURE} />
      </TestProvider>,
    );

    await waitFor(() => {
      const message = screen.getByText(/3 runs will be re\-executed \. do you wish to continue\?/i);
      expect(message).toBeVisible();
      expect(within(message).getByText(/from failure/i)).toBeVisible();
    });
  });

  it('moves into loading state upon re-execution', async () => {
    render(
      <TestProvider>
        <Test strategy={ReexecutionStrategy.FROM_FAILURE} />
      </TestProvider>,
    );

    await waitFor(() => {
      const message = screen.getByText(/3 runs will be re\-executed \. do you wish to continue\?/i);
      expect(message).toBeVisible();
      expect(within(message).getByText(/from failure/i)).toBeVisible();
    });

    const button = screen.getByText(/re\-execute 3 runs/i);
    userEvent.click(button);

    await waitFor(() => {
      expect(
        screen.getByText(/Please do not close the window or navigate away during re-execution./i),
      ).toBeVisible();
      expect(screen.getByRole('button', {name: /Re-executing 3 runs.../i})).toBeVisible();
    });
  });

  it('displays success message if mutations are successful', async () => {
    const mocks = {
      LaunchRunReexecutionResult: () => ({
        __typename: 'LaunchRunSuccess',
      }),
    };

    render(
      <TestProvider apolloProps={{mocks: [mocks]}}>
        <Test strategy={ReexecutionStrategy.FROM_FAILURE} />
      </TestProvider>,
    );

    await waitFor(() => {
      const button = screen.getByText(/re\-execute 3 runs/i);
      userEvent.click(button);
    });

    await waitFor(() => {
      expect(screen.getByText(/Successfully requested re-execution for 3 runs./i)).toBeVisible();
    });
  });

  it('displays python errors', async () => {
    const mocks = {
      LaunchRunReexecutionResult: () => ({
        __typename: 'PythonError',
      }),
    };

    render(
      <TestProvider apolloProps={{mocks: [mocks]}}>
        <Test strategy={ReexecutionStrategy.FROM_FAILURE} />
      </TestProvider>,
    );

    await waitFor(() => {
      const button = screen.getByText(/re\-execute 3 runs/i);
      userEvent.click(button);
    });

    await waitFor(() => {
      expect(screen.getAllByText(/A wild python error appeared!/i)).toHaveLength(3);
    });
  });
});
