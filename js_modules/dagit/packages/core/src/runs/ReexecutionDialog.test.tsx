import {gql, useQuery} from '@apollo/client';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {ReexecutionDialog} from './ReexecutionDialog';
import {RUN_TABLE_RUN_FRAGMENT} from './RunTable';
import {ReexecutionDialogTestQuery} from './types/ReexecutionDialogTestQuery';

describe('ReexecutionDialog', () => {
  const defaultMocks = {
    RepositoryOrigin: () => ({
      repositoryName: () => 'foo',
      repositoryLocationName: () => 'bar',
    }),
    Workspace: () => ({
      locationEntries: () => [...new Array(1)],
    }),
    Repository: () => ({
      id: () => 'foo',
      name: () => 'foo',
      pipelines: () => [{id: 'my_pipeline', name: 'my_pipeline'}],
    }),
    RepositoryLocation: () => ({
      id: () => 'bar',
      name: () => 'bar',
      repositories: () => [...new Array(1)],
    }),
    Run: () => ({
      pipelineName: () => 'my_pipeline',
    }),
    Runs: () => ({
      results: () => [...new Array(3)],
    }),
  };

  const Test = () => {
    const {data} = useQuery<ReexecutionDialogTestQuery>(REEXECUTION_DIALOG_TEST_QUERY);
    const runs = data?.pipelineRunsOrError;

    if (!runs || runs.__typename !== 'Runs' || !runs.results?.length) {
      return null;
    }

    const selectedMap = runs.results.reduce((accum, run) => ({...accum, [run.id]: run}), {});

    return (
      <ReexecutionDialog
        isOpen
        onClose={jest.fn()}
        onComplete={jest.fn()}
        selectedRuns={selectedMap}
      />
    );
  };

  it('prompts the user with the number of runs to re-execute', async () => {
    render(
      <TestProvider apolloProps={{mocks: [defaultMocks]}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/3 runs will be re\-executed from failure\. do you wish to continue\?/i),
      ).toBeVisible();
    });
  });

  it('moves into loading state upon re-execution', async () => {
    render(
      <TestProvider apolloProps={{mocks: [defaultMocks]}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/3 runs will be re\-executed\ from failure. do you wish to continue\?/i),
      ).toBeVisible();
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
      <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
        <Test />
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
      <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
        <Test />
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

const REEXECUTION_DIALOG_TEST_QUERY = gql`
  query ReexecutionDialogTestQuery {
    pipelineRunsOrError(limit: 3) {
      ... on Runs {
        results {
          id
          ...RunTableRunFragment
        }
      }
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
`;
