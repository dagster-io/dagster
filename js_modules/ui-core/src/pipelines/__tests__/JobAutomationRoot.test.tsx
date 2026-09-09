import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {Route} from '../../app/Route';
import {
  buildAssetConditionEvaluation,
  buildAssetConditionEvaluationRecord,
  buildAssetConditionEvaluationRecords,
  buildPartitionSet,
  buildPartitionedAssetConditionEvaluationNode,
  buildRepository,
} from '../../graphql/builders';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {JOB_AUTOMATION_LIST_QUERY, JobAutomationRoot} from '../JobAutomationRoot';

const mockUseRepository = jest.fn();
jest.mock('../../workspace/WorkspaceContext/util', () => ({
  ...jest.requireActual('../../workspace/WorkspaceContext/util'),
  useRepository: (...args: unknown[]) => mockUseRepository(...args),
}));

const JOB_NAME = 'demo_job';
const repoAddress = buildRepoAddress('foo', 'bar');

const buildListMock = (
  records: ReturnType<typeof buildAssetConditionEvaluationRecord>[],
): MockedResponse => ({
  request: {
    query: JOB_AUTOMATION_LIST_QUERY,
    variables: {assetJobKey: {jobName: JOB_NAME}, cursor: undefined, limit: 31},
  },
  result: {
    data: {
      __typename: 'Query',
      assetConditionEvaluationRecordsOrError: buildAssetConditionEvaluationRecords({records}),
    },
  },
});

const renderRoot = (mocks: MockedResponse[]) =>
  render(
    <RecoilRoot>
      <MockedProvider mocks={mocks}>
        <MemoryRouter initialEntries={[`/locations/bar/jobs/${JOB_NAME}/automation`]}>
          <Route path="/locations/:repoPath/jobs/:pipelinePath/automation">
            <JobAutomationRoot repoAddress={repoAddress} />
          </Route>
        </MemoryRouter>
      </MockedProvider>
    </RecoilRoot>,
  );

describe('JobAutomationRoot', () => {
  beforeEach(() => {
    mockUseRepository.mockReset();
    mockUseRepository.mockReturnValue({repository: buildRepository({partitionSets: []})});
  });

  it('renders the empty state when the job has no evaluations', async () => {
    renderRoot([buildListMock([])]);
    expect(await screen.findByText(/no evaluations/i)).toBeVisible();
  });

  it('renders evaluation rows for an unpartitioned job', async () => {
    const record = buildAssetConditionEvaluationRecord({
      id: 'e1',
      evaluationId: '1',
      numRequested: 1,
      runIds: ['run1'],
    });
    renderRoot([buildListMock([record])]);

    // unpartitioned rendering: a plain "Requested" tag, no partition count
    expect(await screen.findByText('Requested')).toBeVisible();
  });

  it('detects a partitioned job via the repository partition sets', async () => {
    mockUseRepository.mockReturnValue({
      repository: buildRepository({
        partitionSets: [buildPartitionSet({pipelineName: JOB_NAME})],
      }),
    });

    const record = buildAssetConditionEvaluationRecord({
      id: 'e1',
      evaluationId: '1',
      numRequested: 2,
      runIds: ['run1', 'run2'],
      evaluation: buildAssetConditionEvaluation({
        rootUniqueId: 'root',
        evaluationNodes: [
          buildPartitionedAssetConditionEvaluationNode({uniqueId: 'root', numTrue: 2}),
        ],
      }),
    });
    renderRoot([buildListMock([record])]);

    // partitioned rendering: the requested-count tag with the partition popover
    expect(await screen.findByText(/2 requested/)).toBeVisible();
  });
});
