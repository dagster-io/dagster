import {gql, useQuery} from '@apollo/client';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TimezoneProvider} from 'src/app/time/TimezoneContext';
import {RunDetails, RUN_DETAILS_FRAGMENT} from 'src/runs/RunDetails';
import {RunDetailsTestQuery} from 'src/runs/types/RunDetailsTestQuery';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {PipelineRunStatus} from 'src/types/globalTypes';

jest.mock('src/app/time/browserTimezone.ts', () => ({
  browserTimezone: () => 'US/Pacific',
}));

describe('RunDetails', () => {
  const RUN_DETAILS_TEST_QUERY = gql`
    query RunDetailsTestQuery {
      pipelineRunOrError(runId: "abc") {
        ... on PipelineRun {
          id
          ...RunDetailsFragment
        }
      }
    }
    ${RUN_DETAILS_FRAGMENT}
  `;

  const Test = () => {
    const {data, loading} = useQuery<RunDetailsTestQuery>(RUN_DETAILS_TEST_QUERY, {
      fetchPolicy: 'no-cache',
    });

    if (
      !data ||
      !data?.pipelineRunOrError ||
      data?.pipelineRunOrError.__typename !== 'PipelineRun'
    ) {
      return null;
    }
    return <RunDetails loading={loading} run={data.pipelineRunOrError} />;
  };

  type MockConfig = {
    status: PipelineRunStatus;
    startTime: number | null;
    endTime: number | null;
  };

  const buildMocks = (config: MockConfig) => {
    const {status, startTime, endTime} = config;
    return {
      PipelineRunOrError: () => ({
        __typename: 'PipelineRun',
      }),
      PipelineRunStatsOrError: () => ({
        __typename: 'PipelineRunStatsSnapshot',
      }),
      PipelineRun: () => ({
        id: () => 'abc',
        status: () => status,
      }),
      PipelineRunStatsSnapshot: () => ({
        id: () => 'abc-time',
        startTime: () => startTime,
        endTime: () => endTime,
      }),
    };
  };

  const START_TIME = 1613571870.934;
  const END_TIME = 1613571916.945;
  const FAKE_NOW = 1613571931.945; // Fifteen seconds later

  const renderAll = (config: MockConfig) => {
    return render(
      <ApolloTestProvider mocks={buildMocks(config)}>
        <TimezoneProvider>
          <Test />
        </TimezoneProvider>
      </ApolloTestProvider>,
    );
  };

  let dateNow: any = null;
  beforeEach(() => {
    jest.useFakeTimers();
    dateNow = global.Date.now;
    const dateNowStub = jest.fn(() => FAKE_NOW * 1000);
    global.Date.now = dateNowStub;
  });

  afterEach(() => {
    jest.useRealTimers();
    global.Date.now = dateNow;
  });

  it('renders QUEUED details', async () => {
    renderAll({status: PipelineRunStatus.QUEUED, startTime: null, endTime: null});

    await waitFor(() => {
      // Validate some basic pieces of the structure.
      expect(screen.getByRole('table')).toBeVisible();

      const rows = screen.getAllByRole('row');
      expect(rows).toHaveLength(3);

      expect(screen.getByRole('row', {name: /started queued/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended queued/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration queued/i})).toBeVisible();
    });
  });

  it('renders CANCELED details with start time', async () => {
    renderAll({
      status: PipelineRunStatus.CANCELED,
      startTime: START_TIME,
      endTime: END_TIME,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started feb 17, 2021, 6:24:30 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended feb 17, 2021, 6:25:16 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration time 0:00:46/i})).toBeVisible();
    });
  });

  it('renders CANCELED details without start time', async () => {
    renderAll({
      status: PipelineRunStatus.CANCELED,
      startTime: null,
      endTime: END_TIME,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started canceled/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended feb 17, 2021, 6:25:16 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration canceled/i})).toBeVisible();
    });
  });

  it('renders CANCELING details', async () => {
    renderAll({
      status: PipelineRunStatus.CANCELING,
      startTime: START_TIME,
      endTime: null,
    });

    await waitFor(() => {
      jest.runTimersToTime(5000);
      expect(screen.getByRole('row', {name: /started feb 17, 2021, 6:24:30 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended canceling/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration time 0:01:01/i})).toBeVisible();
    });
  });

  it('renders FAILURE details with start time', async () => {
    renderAll({
      status: PipelineRunStatus.FAILURE,
      startTime: START_TIME,
      endTime: END_TIME,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started feb 17, 2021, 6:24:30 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended feb 17, 2021, 6:25:16 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration time 0:00:46/i})).toBeVisible();
    });
  });

  it('renders FAILURE details without start time', async () => {
    renderAll({
      status: PipelineRunStatus.FAILURE,
      startTime: null,
      endTime: END_TIME,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started failed/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended feb 17, 2021, 6:25:16 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration failed/i})).toBeVisible();
    });
  });

  it('renders NOT_STARTED details', async () => {
    renderAll({
      status: PipelineRunStatus.NOT_STARTED,
      startTime: null,
      endTime: null,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started waiting to start…/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended waiting to start…/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration waiting to start…/i})).toBeVisible();
    });
  });

  it('renders STARTED details', async () => {
    renderAll({
      status: PipelineRunStatus.STARTED,
      startTime: START_TIME,
      endTime: null,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started feb 17, 2021, 6:24:30 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended running…/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration time 0:01:01/i})).toBeVisible();
    });
  });

  it('renders STARTING details with start time', async () => {
    renderAll({
      status: PipelineRunStatus.STARTING,
      startTime: START_TIME,
      endTime: null,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started feb 17, 2021, 6:24:30 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended starting…/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration time 0:01:01/i})).toBeVisible();
    });
  });

  it('renders STARTING details without start time', async () => {
    renderAll({
      status: PipelineRunStatus.STARTING,
      startTime: null,
      endTime: null,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started starting…/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended starting…/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration starting…/i})).toBeVisible();
    });
  });

  it('renders SUCCEESS details', async () => {
    renderAll({
      status: PipelineRunStatus.SUCCESS,
      startTime: START_TIME,
      endTime: END_TIME,
    });

    await waitFor(() => {
      expect(screen.getByRole('row', {name: /started feb 17, 2021, 6:24:30 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /ended feb 17, 2021, 6:25:16 am/i})).toBeVisible();
      expect(screen.getByRole('row', {name: /duration time 0:00:46/i})).toBeVisible();
    });
  });
});
