import {render} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {useQuery} from '../../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {buildRun, buildRunGroup} from '../../graphql/builders';
import {RunStatus} from '../../graphql/types';
import {RunGroupPanel} from '../RunGroupPanel';

jest.mock('../../apollo-client', () => ({
  ...jest.requireActual('../../apollo-client'),
  useQuery: jest.fn(),
}));
jest.mock('../../app/QueryRefresh', () => ({
  ...jest.requireActual('../../app/QueryRefresh'),
  useQueryRefreshAtInterval: jest.fn(),
}));

const mockUseQuery = useQuery as jest.Mock;
const mockUseQueryRefreshAtInterval = useQueryRefreshAtInterval as jest.Mock;

const runWithStatus = (id: string, status: RunStatus) =>
  buildRun({
    id,
    status,
    tags: [],
    startTime: 1,
    endTime: status === RunStatus.STARTED ? null : 2,
    updateTime: 2,
  });

const renderWithRuns = (statuses: RunStatus[]) => {
  mockUseQuery.mockReturnValue({
    data: {
      runGroupOrError: buildRunGroup({
        rootRunId: 'run-0',
        runs: statuses.map((status, ii) => runWithStatus(`run-${ii}`, status)),
      }),
    },
    refetch: jest.fn(),
  });
  render(
    <MemoryRouter>
      <RunGroupPanel runId="run-0" runStatusLastChangedAt={0} />
    </MemoryRouter>,
  );
  return mockUseQueryRefreshAtInterval.mock.calls.at(-1)?.[1];
};

describe('RunGroupPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('refreshes every 15s while a run in the group is in progress', () => {
    expect(renderWithRuns([RunStatus.SUCCESS, RunStatus.STARTED])).toBe(FIFTEEN_SECONDS);
  });

  it('refreshes rarely once every run in the group has finished', () => {
    expect(renderWithRuns([RunStatus.SUCCESS, RunStatus.FAILURE])).toBeGreaterThan(FIFTEEN_SECONDS);
  });
});
