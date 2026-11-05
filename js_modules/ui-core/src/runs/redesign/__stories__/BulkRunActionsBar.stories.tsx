import {MockedProvider} from '@apollo/client/testing';
import {useState} from 'react';

import {
  buildDeletePipelineRunSuccess,
  buildRun,
  buildTerminateRunSuccess,
  buildTerminateRunsResult,
} from '../../../graphql/builders';
import {ReexecutionStrategy, RunStatus, TerminateRunPolicy} from '../../../graphql/types';
import {tagsWithUIExecutionTags} from '../../../launchpad/uiExecutionTags';
import {buildMutationMock} from '../../../testing/mocking';
import {DELETE_MUTATION, TERMINATE_MUTATION} from '../../RunUtils';
import {buildLaunchPipelineReexecutionSuccessMock} from '../../__fixtures__/Reexecution.fixtures';
import {
  DeleteMutation,
  DeleteMutationVariables,
  TerminateMutation,
  TerminateMutationVariables,
} from '../../types/RunUtils.types';
import {BulkRunActionsBar} from '../BulkRunActionsBar';
import {runEntry} from '../__fixtures__/RunsFeedEntries.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/BulkRunActionsBar',
  component: BulkRunActionsBar,
};

const SUCCESS_RUN = runEntry({
  id: 'a1b2c3d4-1111-2222-3333-444455556666',
  hasDeletePermission: true,
});
const FAILURE_RUN = runEntry({
  id: 'b2c3d4e5-1111-2222-3333-444455556666',
  runStatus: RunStatus.FAILURE,
  hasDeletePermission: true,
});
const STARTED_RUN = runEntry({
  id: 'c3d4e5f6-1111-2222-3333-444455556666',
  runStatus: RunStatus.STARTED,
  endTime: null,
  hasDeletePermission: true,
});
const PAGE_RUNS = [SUCCESS_RUN, FAILURE_RUN, STARTED_RUN];

const buildDeleteMock = (runId: string) =>
  buildMutationMock<DeleteMutation, DeleteMutationVariables>({
    query: DELETE_MUTATION,
    variables: {runId},
    data: {deletePipelineRun: buildDeletePipelineRunSuccess({runId})},
  });

const buildTerminateMock = (runId: string, terminatePolicy: TerminateRunPolicy) =>
  buildMutationMock<TerminateMutation, TerminateMutationVariables>({
    query: TERMINATE_MUTATION,
    variables: {runIds: [runId], terminatePolicy},
    data: {
      terminateRuns: buildTerminateRunsResult({
        terminateRunResults: [buildTerminateRunSuccess({run: buildRun({id: runId})})],
      }),
    },
  });

const buildReexecuteMock = (parentRunId: string, strategy: ReexecutionStrategy) =>
  buildLaunchPipelineReexecutionSuccessMock({
    parentRunId,
    strategy,
    extraTags: tagsWithUIExecutionTags([]),
  });

// Every action the page's runs enable, so confirming one works after check-all too.
const ACTION_MOCKS = [
  buildDeleteMock(SUCCESS_RUN.id),
  buildDeleteMock(FAILURE_RUN.id),
  buildDeleteMock(STARTED_RUN.id),
  buildTerminateMock(STARTED_RUN.id, TerminateRunPolicy.SAFE_TERMINATE),
  buildTerminateMock(STARTED_RUN.id, TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY),
  buildReexecuteMock(SUCCESS_RUN.id, ReexecutionStrategy.ALL_STEPS),
  buildReexecuteMock(FAILURE_RUN.id, ReexecutionStrategy.ALL_STEPS),
  buildReexecuteMock(FAILURE_RUN.id, ReexecutionStrategy.FROM_FAILURE),
];

type SelectionBarTemplateProps = {
  initialSelectedIds: string[];
};

const SelectionBarTemplate = ({initialSelectedIds}: SelectionBarTemplateProps) => {
  const [selectedIds, setSelectedIds] = useState(initialSelectedIds);
  const selectedRuns = PAGE_RUNS.filter((run) => selectedIds.includes(run.id));

  return (
    <MockedProvider mocks={ACTION_MOCKS}>
      <BulkRunActionsBar
        selectedRuns={selectedRuns}
        pageRunCount={PAGE_RUNS.length}
        onToggleAll={(checked) => setSelectedIds(checked ? PAGE_RUNS.map((run) => run.id) : [])}
        clearSelection={() => setSelectedIds([])}
        onClose={() => setSelectedIds([])}
      />
    </MockedProvider>
  );
};

export const SomeRunsSelected = () => (
  <SelectionBarTemplate initialSelectedIds={[SUCCESS_RUN.id, FAILURE_RUN.id]} />
);

export const NoRunsSelected = () => <SelectionBarTemplate initialSelectedIds={[]} />;
