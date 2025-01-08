import {
  Box,
  Caption,
  CollapsibleSection,
  Colors,
  ExternalAnchorButton,
  FontFamily,
  NonIdealState,
  Subtitle1,
  Subtitle2,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {
  AssetCheckEvaluationTargetMaterializationFragment,
  AssetCheckExecutionFragment,
} from './types/AssetCheckDetailDialog.types';
import {AssetCheckTableFragment} from './types/VirtualizedAssetCheckTable.types';
import {Timestamp} from '../../app/time/Timestamp';
import {MetadataEntries} from '../../metadata/MetadataEntry';
import {Description} from '../../pipelines/Description';
import {linkToRunEvent} from '../../runs/RunUtils';
import {AssetMaterializationGraphs} from '../AssetMaterializationGraphs';

interface Props {
  selectedCheck: AssetCheckTableFragment;
  lastExecution: AssetCheckExecutionFragment | null;
  targetMaterialization: AssetCheckEvaluationTargetMaterializationFragment | null;
  executions: AssetCheckExecutionFragment[];
  executionsLoading: boolean;
}

export const AssetCheckOverview = ({
  selectedCheck,
  lastExecution,
  targetMaterialization,
  executions,
  executionsLoading,
}: Props) => {
  const executionPlotGroups = useMemo(
    () =>
      executions
        .filter((e) => e.evaluation)
        .map((e) => ({
          metadataEntries: e.evaluation!.metadataEntries,
          timestamp: `${Math.round(e.evaluation!.timestamp * 1000)}`,
        }))
        .map((e) => ({latest: e, all: [e], timestamp: e.timestamp})),
    [executions],
  );

  return (
    <Box
      flex={{grow: 1, direction: 'column', gap: 12}}
      padding={{horizontal: 24, top: 4, bottom: 12}}
    >
      <CollapsibleSection
        headerWrapperProps={headerWrapperProps}
        header={<Subtitle1>About</Subtitle1>}
        arrowSide="right"
      >
        <Box padding={{top: 12}} flex={{gap: 12, direction: 'column'}}>
          {selectedCheck.description ? (
            <Description description={selectedCheck.description} maxHeight={260} />
          ) : (
            <Caption color={Colors.textLight()}>No description provided</Caption>
          )}
        </Box>
      </CollapsibleSection>
      <CollapsibleSection
        headerWrapperProps={headerWrapperProps}
        header={<Subtitle1>Latest execution</Subtitle1>}
        arrowSide="right"
      >
        {lastExecution?.evaluation?.description ? (
          <Box padding={{top: 12}} flex={{gap: 12, direction: 'column'}}>
            <Description description={lastExecution.evaluation.description} maxHeight={260} />
          </Box>
        ) : null}
        <Box padding={{top: 12}} flex={{direction: 'column', gap: 20}}>
          <Box flex={{direction: 'row', gap: 48}}>
            <Box flex={{direction: 'column', gap: 8}}>
              <Subtitle2>Evaluation result</Subtitle2>
              <div>
                <AssetCheckStatusTag execution={selectedCheck.executionForLatestMaterialization} />
              </div>
            </Box>
            {lastExecution ? (
              <Box flex={{direction: 'column', gap: 8}}>
                <Subtitle2>Timestamp</Subtitle2>
                <Link
                  to={linkToRunEvent(
                    {id: lastExecution.runId},
                    {stepKey: lastExecution.stepKey, timestamp: lastExecution.timestamp},
                  )}
                >
                  <Timestamp timestamp={{unix: lastExecution.timestamp}} />
                </Link>
              </Box>
            ) : null}
            {targetMaterialization ? (
              <Box flex={{direction: 'column', gap: 8}}>
                <Subtitle2>Target materialization</Subtitle2>
                <Link to={`/runs/${targetMaterialization.runId}`}>
                  <Timestamp timestamp={{unix: targetMaterialization.timestamp}} />
                </Link>
              </Box>
            ) : null}
          </Box>
          {lastExecution?.evaluation?.metadataEntries.length ? (
            <Box flex={{direction: 'column', gap: 8}}>
              <Subtitle2>Metadata</Subtitle2>
              <div style={{fontFamily: FontFamily.monospace, fontSize: 12}}>
                <MetadataEntries entries={lastExecution.evaluation.metadataEntries} />
              </div>
            </Box>
          ) : null}
        </Box>
      </CollapsibleSection>
      <CollapsibleSection
        header={<Subtitle1>Plots</Subtitle1>}
        headerWrapperProps={headerWrapperProps}
        isInitiallyCollapsed={executionsLoading || executionPlotGroups.length === 0}
        key={`reset-collapsed-on-load-${executionsLoading}`}
        arrowSide="right"
      >
        <AssetMaterializationGraphs
          xAxis="time"
          groups={executionPlotGroups}
          emptyState={
            <Box padding={{horizontal: 24, vertical: 24}}>
              <NonIdealState
                shrinkable
                icon="asset_plot"
                title="Plots are automatically generated by metadata"
                description="Include numeric metadata entries in your check metadata to see data graphed."
                action={
                  <ExternalAnchorButton href="https://docs.dagster.io/concepts/metadata-tags/asset-metadata">
                    View documentation
                  </ExternalAnchorButton>
                }
              />
            </Box>
          }
        />
      </CollapsibleSection>
    </Box>
  );
};

const headerWrapperProps: React.ComponentProps<typeof Box> = {
  border: 'bottom',
  padding: {vertical: 12},
  style: {
    cursor: 'pointer',
  },
};
