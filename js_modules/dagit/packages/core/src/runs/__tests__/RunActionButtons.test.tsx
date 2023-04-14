import {useQuery} from '@apollo/client';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {RunStatus} from '../../graphql/types';
import {TestProvider} from '../../testing/TestProvider';
import {RunActionButtons} from '../RunActionButtons';

import {RUN_ACTION_BUTTONS_TEST_QUERY} from './RunActionButtonsTestQuery';
import {
  RunActionButtonsTestQuery,
  RunActionButtonsTestQueryVariables,
} from './types/RunActionButtonsTestQuery.types';

describe('RunActionButtons', () => {
  const props = {
    selection: {
      keys: [],
      query: '',
    },
    graph: [],
    metadata: {
      firstLogAt: 0,
      mostRecentLogAt: 0,
      globalMarkers: [],
      steps: {},
    },
    onLaunch: jest.fn(),
  };

  const Test = () => {
    const {data} = useQuery<RunActionButtonsTestQuery, RunActionButtonsTestQueryVariables>(
      RUN_ACTION_BUTTONS_TEST_QUERY,
    );
    if (data) {
      const run = data.pipelineRunOrError;
      if (run.__typename === 'Run') {
        return <RunActionButtons {...props} run={run} />;
      }
      return <div>Error</div>;
    }
    return <div>Loading</div>;
  };

  const defaultMocks = {
    RunConfigData: () => 'foo',
  };

  describe('`Terminate` button', () => {
    it('is visible for `STARTED` runs', async () => {
      const mocks = {
        Run: () => ({
          status: () => RunStatus.STARTED,
        }),
      };

      render(
        <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
          <Test />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(
          screen.queryByRole('button', {
            name: /terminate/i,
          }),
        ).toBeVisible();
      });
    });

    it('is visible for `STARTING` runs', async () => {
      const mocks = {
        Run: () => ({
          status: () => RunStatus.STARTING,
        }),
      };

      render(
        <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
          <Test />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(
          screen.queryByRole('button', {
            name: /terminate/i,
          }),
        ).toBeVisible();
      });
    });

    it('is NOT visible for `FAILURE` runs', async () => {
      const mocks = {
        Run: () => ({
          status: () => RunStatus.FAILURE,
        }),
      };

      render(
        <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
          <Test />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(
          screen.queryByRole('button', {
            name: /terminate/i,
          }),
        ).toBeNull();
      });
    });

    it('is NOT visible for `CANCELED` runs', async () => {
      const mocks = {
        Run: () => ({
          status: () => RunStatus.CANCELED,
        }),
      };

      render(
        <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
          <Test />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(
          screen.queryByRole('button', {
            name: /terminate/i,
          }),
        ).toBeNull();
      });
    });

    it('is NOT visible for `SUCCESS` runs', async () => {
      const mocks = {
        Run: () => ({
          status: () => RunStatus.SUCCESS,
        }),
      };

      render(
        <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
          <Test />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(
          screen.queryByRole('button', {
            name: /terminate/i,
          }),
        ).toBeNull();
      });
    });
  });
});
