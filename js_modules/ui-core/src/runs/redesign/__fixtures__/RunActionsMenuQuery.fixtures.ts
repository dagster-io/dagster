import {buildExecutionPlan, buildRun} from '../../../graphql/builders';
import {buildQueryMock} from '../../../testing/mocking';
import {RUN_ACTIONS_MENU_QUERY} from '../RunActionsMenuQuery';
import {
  RunActionsMenuQuery,
  RunActionsMenuQueryVariables,
} from '../types/RunActionsMenuQuery.types';
import {RunSummaryFragment} from '../types/RunsFeedFragments.types';

type MenuRun = Pick<
  RunSummaryFragment,
  'id' | 'assetSelectionPreview' | 'assetCheckSelectionPreview'
>;

// Uses the row's previews as the full selection, so View asset selection matches the row's tags.
export const buildActionsMenuQueryMock = ({
  id,
  assetSelectionPreview,
  assetCheckSelectionPreview,
}: MenuRun) =>
  buildQueryMock<RunActionsMenuQuery, RunActionsMenuQueryVariables>({
    query: RUN_ACTIONS_MENU_QUERY,
    variables: {runId: id},
    data: {
      runOrError: buildRun({
        id,
        parentPipelineSnapshotId: null,
        runConfigYaml: '{}\n',
        assetSelection: assetSelectionPreview,
        assetCheckSelection: assetCheckSelectionPreview,
        executionPlan: buildExecutionPlan({assetKeys: []}),
      }),
    },
    maxUsageCount: Number.POSITIVE_INFINITY,
  });
