import qs from 'query-string';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntry} from '../runs/MetadataEntry';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {IconWIP, IconWrapper} from '../ui/Icon';
import {Table} from '../ui/Table';
import {Mono} from '../ui/Text';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetLineageElements} from './AssetLineageElements';
import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {HistoricalMaterialization} from './useMaterializationBuckets';

export const AssetMaterializationTable: React.FC<{
  hasPartitions: boolean;
  hasLineage: boolean;
  materializations: HistoricalMaterialization[];
  focused?: string;
  setFocused?: (timestamp: string) => void;
}> = ({hasPartitions, hasLineage, materializations, focused, setFocused}) => {
  return (
    <Table>
      <thead>
        <tr>
          {hasPartitions && <th style={{minWidth: 100}}>Partition</th>}
          <th style={{minWidth: 150}}>Timestamp</th>
          <th style={{minWidth: 150}}>Job / Pipeline</th>
          <th style={{width: 100}}>Run</th>
        </tr>
      </thead>
      <tbody>
        {materializations.map((m) => (
          <AssetMaterializationRow
            key={m.latest.materializationEvent.timestamp}
            hasPartitions={hasPartitions}
            hasLineage={hasLineage}
            assetMaterialization={m}
            focused={focused}
            setFocused={setFocused}
          />
        ))}
      </tbody>
    </Table>
  );
};

const AssetMaterializationRow: React.FC<{
  assetMaterialization: HistoricalMaterialization;
  hasPartitions: boolean;
  hasLineage: boolean;
  focused?: string;
  setFocused?: (timestamp: string) => void;
}> = ({assetMaterialization, hasPartitions, hasLineage, focused, setFocused}) => {
  const {latest, predecessors} = assetMaterialization;
  const run = latest.runOrError.__typename === 'Run' ? latest.runOrError : undefined;
  const repositoryOrigin = run?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  if (!run) {
    return <span />;
  }
  const {materialization, assetLineage, timestamp, stepKey} = latest.materializationEvent;
  const metadataEntries = materialization.metadataEntries;
  const isFocused = focused === timestamp;

  const focusCss = isFocused
    ? {paddingLeft: 4, borderLeft: `4px solid ${ColorsWIP.HighlightGreen}`}
    : {paddingLeft: 8};

  return (
    <>
      <HoverableRow>
        {hasPartitions && (
          <td style={{whiteSpace: 'nowrap', ...focusCss}}>
            <Group direction="row" spacing={2}>
              <DisclosureTriangle open={isFocused} onClick={() => setFocused?.(timestamp)} />
              {latest.partition || <span style={{color: ColorsWIP.Gray400}}>None</span>}
            </Group>
          </td>
        )}
        <td style={hasPartitions ? {} : focusCss}>
          <Group direction="row" spacing={4}>
            {!hasPartitions && (
              <DisclosureTriangle open={isFocused} onClick={() => setFocused?.(timestamp)} />
            )}
            <Group direction="column" spacing={4}>
              <Timestamp timestamp={{ms: Number(timestamp)}} />
              {predecessors?.length ? (
                <AssetPredecessorLink
                  hasPartitions={hasPartitions}
                  hasLineage={hasLineage}
                  predecessors={predecessors}
                />
              ) : null}
            </Group>
          </Group>
        </td>
        <td>
          <Box margin={{bottom: 4}}>
            <Box padding={{left: 8}}>
              <PipelineReference
                showIcon
                pipelineName={run.pipelineName}
                pipelineHrefContext={repoAddress || 'repo-unknown'}
                snapshotId={run.pipelineSnapshotId}
                isJob={isThisThingAJob(repo, run.pipelineName)}
              />
            </Box>
            <Group direction="row" padding={{left: 8}} spacing={8} alignItems="center">
              <IconWIP name="linear_scale" color={ColorsWIP.Gray400} />
              <Link
                to={`/instance/runs/${run.runId}?${qs.stringify({
                  selection: stepKey,
                  logs: `step:${stepKey}`,
                })}`}
              >
                {stepKey}
              </Link>
            </Group>
          </Box>
        </td>
        <td>
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <RunStatusWithStats runId={run.runId} status={run.status} />
            <Link to={`/instance/runs/${run.runId}?timestamp=${timestamp}`}>
              <Mono>{titleForRun(run)}</Mono>
            </Link>
          </Box>
        </td>
      </HoverableRow>
      {isFocused && (
        <tr style={{background: ColorsWIP.Gray50}}>
          <td colSpan={6} style={{fontSize: 14, padding: 0}}>
            {materialization.description && (
              <Box padding={{horizontal: 24, vertical: 12}}>{materialization.description}</Box>
            )}
            {metadataEntries.length || hasLineage ? (
              <DetailsTable>
                <tbody>
                  {(metadataEntries || []).map((entry) => (
                    <tr key={`metadata-${entry.label}`}>
                      <td>{entry.label}</td>
                      <td>
                        <MetadataEntry entry={entry} expandSmallValues={true} />
                      </td>
                    </tr>
                  ))}
                  {hasLineage && (
                    <tr>
                      <td>Parent Materializations</td>
                      <td>
                        <AssetLineageElements elements={assetLineage} timestamp={timestamp} />
                      </td>
                    </tr>
                  )}
                </tbody>
              </DetailsTable>
            ) : (
              <Box padding={{horizontal: 24, vertical: 12}}>No materialization event metadata</Box>
            )}
          </td>
        </tr>
      )}
    </>
  );
};

const HoverableRow = styled.tr`
  &:hover {
    background: ${ColorsWIP.Gray10};
  }
`;

const DetailsTable = styled.table`
  margin: -2px -2px -3px;
  tr td {
    font-size: 14px;
  }
`;

interface PredecessorDialogProps {
  hasLineage: boolean;
  hasPartitions: boolean;
  predecessors: AssetMaterializationFragment[];
}

export const AssetPredecessorLink: React.FC<PredecessorDialogProps> = ({
  hasLineage,
  hasPartitions,
  predecessors,
}) => {
  const [open, setOpen] = React.useState(false);
  const count = predecessors.length;
  const title = () => {
    if (hasPartitions) {
      const partition = predecessors[0].partition;
      if (partition) {
        return `Previous materializations for ${partition}`;
      }
    }
    return `Previous materializations`;
  };

  return (
    <>
      <ButtonLink onClick={() => setOpen(true)}>{`View ${count} previous`}</ButtonLink>
      <DialogWIP
        isOpen={open}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setOpen(false)}
        style={{width: '80%', minWidth: '800px'}}
        title={title()}
      >
        <Box padding={{bottom: 8}}>
          <AssetMaterializationTable
            hasLineage={hasLineage}
            hasPartitions={hasPartitions}
            materializations={predecessors.map((p) => ({
              latest: p,
              timestamp: p.materializationEvent.timestamp,
            }))}
          />
        </Box>
        <DialogFooter>
          <ButtonWIP intent="primary" onClick={() => setOpen(false)}>
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
    </>
  );
};

const DisclosureTriangle: React.FC<{open: boolean; onClick: () => void}> = ({open, onClick}) => (
  <DisclosureTriangleButton onClick={onClick} $open={open}>
    <IconWIP name="arrow_drop_down" size={24} />
  </DisclosureTriangleButton>
);

const DisclosureTriangleButton = styled.button<{$open: boolean}>`
  padding: 4px;
  margin: -4px;
  cursor: pointer;
  border: 0;
  background: transparent;
  outline: none;

  ${IconWrapper} {
    margin: -2px -5px;
    transform: ${({$open}) => ($open ? 'rotate(0deg)' : 'rotate(-90deg)')};
    opacity: 0.25;
  }

  :focus {
    outline: none;

    ${IconWrapper} {
      background: ${ColorsWIP.Dark};
      opacity: 0.5;
    }
  }
`;
