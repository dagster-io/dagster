import {render} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {useQuery} from '../../apollo-client';
import {Route} from '../../app/Route';
import {buildRun} from '../../graphql/builders';
import {LogsProvider, LogsProviderLogs} from '../LogsProvider';
import {Run} from '../Run';
import {RunRoot} from '../RunRoot';

const mockLogs: LogsProviderLogs = {
  allNodeChunks: [],
  counts: {DEBUG: 0, INFO: 0, WARNING: 0, ERROR: 0, CRITICAL: 0, EVENT: 0},
  loading: true,
};
const mockLogsProviderMounts = jest.fn();

jest.mock('../../apollo-client', () => ({
  ...jest.requireActual('../../apollo-client'),
  useQuery: jest.fn(),
}));
jest.mock('../LogsProvider', () => ({
  LogsProvider: jest.fn(
    ({runId, children}: {runId: string; children: (logs: LogsProviderLogs) => any}) => {
      jest.requireActual('react').useEffect(() => mockLogsProviderMounts(runId), [runId]);
      return children(mockLogs);
    },
  ),
}));
jest.mock('../Run', () => ({Run: jest.fn(() => null)}));
jest.mock('../RunHeaderActions', () => ({RunHeaderActions: () => null}));
jest.mock('../RunHeaderTags', () => ({RunHeaderTags: () => null}));
jest.mock('../useRunRepoInfo', () => ({
  useRunRepoInfo: () => ({repoAddress: null, isJob: true}),
}));

const mockUseQuery = useQuery as jest.Mock;

const runRootTree = () => (
  <RecoilRoot>
    <MemoryRouter initialEntries={['/runs/abc123']}>
      <Route path="/runs/:runId">
        <RunRoot />
      </Route>
    </MemoryRouter>
  </RecoilRoot>
);

const renderRunRoot = () => render(runRootTree());

describe('RunRoot', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('starts streaming logs before RunRootQuery resolves', () => {
    mockUseQuery.mockReturnValue({data: undefined, loading: true});
    renderRunRoot();

    expect(mockLogsProviderMounts).toHaveBeenCalledWith('abc123');
    expect(Run).not.toHaveBeenCalled();
  });

  it('hands the already-streaming logs to Run once the run loads, without remounting', () => {
    mockUseQuery.mockReturnValue({data: undefined, loading: true});
    const {rerender} = renderRunRoot();

    const run = buildRun({id: 'abc123', runId: 'abc123', tags: []});
    mockUseQuery.mockReturnValue({data: {pipelineRunOrError: run}, loading: false});
    rerender(runRootTree());

    expect(mockLogsProviderMounts).toHaveBeenCalledTimes(1);
    expect(LogsProvider).toHaveBeenCalled();
    expect(Run).toHaveBeenLastCalledWith(
      expect.objectContaining({run, runId: 'abc123', logs: mockLogs}),
      expect.anything(),
    );
  });
});
