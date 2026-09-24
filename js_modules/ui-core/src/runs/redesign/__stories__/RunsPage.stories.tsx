import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {MemoryRouter} from 'react-router-dom';

import {InMemoryCache} from '../../../apollo-client';
import {AnalyticsContext} from '../../../app/analytics';
import {
  buildAssetKey,
  buildPythonError,
  buildRun,
  buildRunStatsSnapshot,
  buildRunsFeedConnection,
} from '../../../graphql/builders';
import possibleTypes from '../../../graphql/possibleTypes.generated.json';
import {RunStatus, RunsFeedView} from '../../../graphql/types';
import {buildQueryMock} from '../../../testing/mocking';
import {RUN_STATS_QUERY} from '../../RunStats';
import {DagsterTag} from '../../RunTag';
import {RunStatsQuery, RunStatsQueryVariables} from '../../types/RunStats.types';
import {RUNS_FEED_QUERY} from '../RunsFeedQuery';
import {RunsPage} from '../RunsPage';
import {buildBackfillSummary, buildRunSummary, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {RunsFeedEntryFragment} from '../types/RunsFeedFragments.types';
import {RunsFeedQuery, RunsFeedQueryVariables} from '../types/RunsFeedQuery.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunsPage',
  component: RunsPage,
};

const NOW = Date.now() / 1000;
const MINUTE = 60;
const HOUR = 60 * MINUTE;
const LOADING_DELAY_MS = 24 * HOUR * 1000;

const ANALYTICS = {page: () => {}, track: () => {}};

const finishedAfter = (seconds: number) => ({
  creationTime: NOW - HOUR - seconds - MINUTE,
  startTime: NOW - HOUR - seconds,
  endTime: NOW - HOUR,
});

const FIRST_PAGE_RUNS = [
  buildRunSummary({
    id: 'cccccccc-1111-2222-3333-444455556666',
    runId: 'cccccccc-1111-2222-3333-444455556666',
    runStatus: RunStatus.STARTED,
    jobName: 'daily_etl',
    creationTime: NOW - 3 * MINUTE,
    startTime: NOW - 2 * MINUTE,
    endTime: null,
  }),
  buildRunSummary({
    id: 'a1b2c3d4-1111-2222-3333-444455556666',
    runId: 'a1b2c3d4-1111-2222-3333-444455556666',
    jobName: 'daily_etl',
    tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')],
    assetSelectionPreview: [buildAssetKey({path: ['sales', 'daily']})],
    assetSelectionCount: 1,
    ...finishedAfter(4 * MINUTE),
  }),
  buildRunSummary({
    id: 'bbbbbbbb-1111-2222-3333-444455556666',
    runId: 'bbbbbbbb-1111-2222-3333-444455556666',
    runStatus: RunStatus.FAILURE,
    jobName: 'daily_etl',
    tags: [tag(DagsterTag.SensorName, 'files_sensor')],
    ...finishedAfter(2 * MINUTE + 12),
  }),
];

const FIRST_PAGE_BACKFILL = buildBackfillSummary({
  id: 'bkfl1234',
  isAssetBackfill: true,
  user: 'pat@example.com',
  creationTime: NOW - 3 * HOUR,
  startTime: NOW - 3 * HOUR,
  endTime: NOW - HOUR,
});

const SECOND_PAGE_RUNS = [
  buildRunSummary({
    id: 'dddddddd-1111-2222-3333-444455556666',
    runId: 'dddddddd-1111-2222-3333-444455556666',
    jobName: 'daily_etl',
    tags: [tag(DagsterTag.User, 'pat@example.com')],
    creationTime: NOW - 5 * HOUR - MINUTE,
    startTime: NOW - 5 * HOUR,
    endTime: NOW - 5 * HOUR + 35,
  }),
];

type FeedMockOptions = {
  cursor?: string;
  delay?: number;
};

const buildFeedMock = (
  runsFeedOrError: RunsFeedQuery['runsFeedOrError'],
  {cursor, delay}: FeedMockOptions = {},
): MockedResponse<RunsFeedQuery, RunsFeedQueryVariables> => ({
  request: {
    query: RUNS_FEED_QUERY,
    variables: {
      limit: 30,
      filter: {},
      view: RunsFeedView.ROOTS,
      ...(cursor === undefined ? {} : {cursor}),
    },
  },
  result: {data: {__typename: 'Query', runsFeedOrError}},
  delay,
  maxUsageCount: Number.POSITIVE_INFINITY,
});

const buildPage = (results: RunsFeedEntryFragment[], hasMore: boolean) => ({
  ...buildRunsFeedConnection({cursor: 'first-page-cursor', hasMore}),
  results,
});

const statsMockFor = (runId: string) =>
  buildQueryMock<RunStatsQuery, RunStatsQueryVariables>({
    query: RUN_STATS_QUERY,
    variables: {runId},
    data: {
      pipelineRunOrError: buildRun({
        id: runId,
        stats: buildRunStatsSnapshot({
          stepsSucceeded: 4,
          stepsFailed: 1,
          materializations: 3,
          expectations: 0,
        }),
      }),
    },
    maxUsageCount: Number.POSITIVE_INFINITY,
  });

const STATS_MOCKS = [...FIRST_PAGE_RUNS, ...SECOND_PAGE_RUNS].map(({id}) => statsMockFor(id));

type PageTemplateProps = {
  mocks: MockedResponse[];
};

const PageTemplate = ({mocks}: PageTemplateProps) => (
  <AnalyticsContext.Provider value={ANALYTICS}>
    <MemoryRouter initialEntries={['/runs']}>
      <MockedProvider mocks={mocks} cache={new InMemoryCache({possibleTypes})}>
        <div style={{height: 640}}>
          <RunsPage />
        </div>
      </MockedProvider>
    </MemoryRouter>
  </AnalyticsContext.Provider>
);

export const Loaded = () => (
  <PageTemplate
    mocks={[
      buildFeedMock(buildPage([...FIRST_PAGE_RUNS, FIRST_PAGE_BACKFILL], true)),
      buildFeedMock(buildPage(SECOND_PAGE_RUNS, false), {cursor: 'first-page-cursor'}),
      ...STATS_MOCKS,
    ]}
  />
);

export const Loading = () => (
  <PageTemplate mocks={[buildFeedMock(buildPage([], false), {delay: LOADING_DELAY_MS})]} />
);

export const Empty = () => <PageTemplate mocks={[buildFeedMock(buildPage([], false))]} />;

export const PythonError = () => (
  <PageTemplate
    mocks={[
      buildFeedMock(
        buildPythonError({
          message: 'Unable to load the runs feed.',
          stack: ['  File "runs_feed.py", line 12, in fetch\n'],
          errorChain: [],
        }),
      ),
    ]}
  />
);
