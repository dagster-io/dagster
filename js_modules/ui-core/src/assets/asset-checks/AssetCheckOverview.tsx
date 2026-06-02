import {
  Box,
  CollapsibleSection,
  Colors,
  ExternalAnchorButton,
  FontFamily,
  Heading,
  Icon,
  NonIdealState,
  Text,
  Tooltip,
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
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          metadataEntries: e.evaluation!.metadataEntries,
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          timestamp: `${Math.round(e.evaluation!.timestamp * 1000)}`,
        }))
        .map((e) => ({latest: e, all: [e], timestamp: e.timestamp})),
    [executions],
  );

  const {blocking} = selectedCheck;

  return (
    <Box
      flex={{grow: 1, direction: 'column', gap: 12}}
      padding={{horizontal: 24, top: 4, bottom: 12}}
    >
      <CollapsibleSection
        headerWrapperProps={headerWrapperProps}
        header={
          <Heading size={16} weight={600}>
            About
          </Heading>
        }
        arrowSide="right"
      >
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}} padding={{top: 12}}>
          <Icon
            name={blocking ? 'shield_check' : 'shield'}
            color={blocking ? Colors.accentYellow() : Colors.accentPrimary()}
          />
          <Text size={12}>
            This is a <strong>{blocking ? 'blocking' : 'non-blocking'}</strong> asset check.
          </Text>
          <Tooltip
            placement="top"
            display="block"
            content={
              <div style={{width: 300}}>
                {blocking
                  ? 'A blocking check prevents downstream asset materializations if the check fails.'
                  : 'A non-blocking check allows downstream asset materializations to proceed regardless of the check result.'}
              </div>
            }
          >
            <Icon name="info" color={Colors.accentGray()} size={12} />
          </Tooltip>
        </Box>
        <Box padding={{top: 12}} flex={{gap: 12, direction: 'column'}}>
          {selectedCheck.description ? (
            <Description description={selectedCheck.description} maxHeight={260} />
          ) : (
            <Text size={12} color="textLight">
              No description provided
            </Text>
          )}
        </Box>
      </CollapsibleSection>
      <CollapsibleSection
        headerWrapperProps={headerWrapperProps}
        header={
          <Heading size={16} weight={600}>
            Latest execution
          </Heading>
        }
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
              <Heading size={14} weight={600}>
                Evaluation result
              </Heading>
              <div>
                <AssetCheckStatusTag execution={selectedCheck.executionForLatestMaterialization} />
              </div>
            </Box>
            {lastExecution ? (
              <Box flex={{direction: 'column', gap: 8}}>
                <Heading size={14} weight={600}>
                  Timestamp
                </Heading>
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
                <Heading size={14} weight={600}>
                  Target materialization
                </Heading>
                <Link to={`/runs/${targetMaterialization.runId}`}>
                  <Timestamp timestamp={{unix: targetMaterialization.timestamp}} />
                </Link>
              </Box>
            ) : null}
            {lastExecution ? (
              <Box flex={{direction: 'column', gap: 8}}>
                <Heading size={14} weight={600}>
                  Partition
                </Heading>
                {lastExecution.evaluation?.partition ? (
                  <div style={{fontFamily: FontFamily.monospace, fontSize: 12}}>
                    {lastExecution.evaluation.partition}
                  </div>
                ) : (
                  <>&mdash;</>
                )}
              </Box>
            ) : null}
          </Box>
          {lastExecution?.evaluation?.metadataEntries.length ? (
            <Box flex={{direction: 'column', gap: 8}}>
              <Heading size={14} weight={600}>
                Metadata
              </Heading>
              <div style={{fontFamily: FontFamily.monospace, fontSize: 12}}>
                <MetadataEntries entries={lastExecution.evaluation.metadataEntries} />
              </div>
            </Box>
          ) : null}
        </Box>
      </CollapsibleSection>
      <CollapsibleSection
        header={
          <Heading size={16} weight={600}>
            Plots
          </Heading>
        }
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
