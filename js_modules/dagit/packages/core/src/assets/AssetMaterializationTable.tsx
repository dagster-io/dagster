import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntries} from '../runs/MetadataEntry';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';
import {Mono} from '../ui/Text';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetLineageElements} from './AssetLineageElements';
import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {HistoricalMaterialization} from './useMaterializationBuckets';

export const AssetMaterializationTable: React.FC<{
  isPartitioned: boolean;
  hasLineage: boolean;
  materializations: HistoricalMaterialization[];
  shouldBucketPartitions?: boolean;
}> = ({isPartitioned, hasLineage, materializations, shouldBucketPartitions = true}) => {
  const list = React.useMemo(() => {
    if (shouldBucketPartitions) {
      return materializations;
    }
    return materializations.map((m) => ({latest: m.latest}));
  }, [materializations, shouldBucketPartitions]);

  return (
    <Table>
      <thead>
        <tr>
          {isPartitioned && <th style={{minWidth: 100}}>Partition</th>}
          <th style={{minWidth: 240}}>Materialization Metadata</th>
          {hasLineage && <th>Parent Materializations</th>}
          <th style={{minWidth: 150}}>Timestamp</th>
          <th style={{minWidth: 150}}>Job / Pipeline</th>
          <th style={{width: 100}}>Run</th>
        </tr>
      </thead>
      <tbody>
        {list.map((m) => (
          <AssetMaterializationRow
            key={m.latest.materializationEvent.timestamp}
            isPartitioned={isPartitioned}
            hasLineage={hasLineage}
            assetMaterialization={m}
          />
        ))}
      </tbody>
    </Table>
  );
};

const AssetMaterializationRow: React.FC<{
  assetMaterialization: HistoricalMaterialization;
  isPartitioned: boolean;
  hasLineage: boolean;
}> = ({assetMaterialization, isPartitioned, hasLineage}) => {
  const {latest, predecessors} = assetMaterialization;
  const run = latest.runOrError.__typename === 'PipelineRun' ? latest.runOrError : undefined;
  const repositoryOrigin = run?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  if (!run) {
    return <span />;
  }
  const {materialization, assetLineage, timestamp} = latest.materializationEvent;
  const metadataEntries = materialization.metadataEntries;

  return (
    <tr>
      {isPartitioned && (
        <td style={{whiteSpace: 'nowrap'}}>
          {latest.partition || <span style={{color: ColorsWIP.Gray400}}>None</span>}
        </td>
      )}
      <td style={{fontSize: 12}}>
        {materialization.description ? (
          <div style={{fontSize: '0.8rem', marginTop: 10}}>{materialization.description}</div>
        ) : null}
        {metadataEntries && metadataEntries.length ? (
          <MetadataTableContainer>
            <MetadataEntries entries={metadataEntries} />
          </MetadataTableContainer>
        ) : null}
      </td>
      {hasLineage && (
        <td>{<AssetLineageElements elements={assetLineage} timestamp={timestamp} />}</td>
      )}
      <td>
        <Group direction="column" spacing={4}>
          <Timestamp timestamp={{ms: Number(timestamp)}} />
          {predecessors?.length ? (
            <AssetPredecessorLink
              isPartitioned={isPartitioned}
              hasLineage={hasLineage}
              predecessors={predecessors}
            />
          ) : null}
        </Group>
      </td>
      <td>
        <PipelineReference
          pipelineName={run.pipelineName}
          pipelineHrefContext={repoAddress || 'repo-unknown'}
          snapshotId={run.pipelineSnapshotId}
          isJob={!!repo && isThisThingAJob(repo, run.pipelineName)}
        />
      </td>
      <td>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <RunStatusWithStats runId={run.runId} status={run.status} />
          <Link to={`/instance/runs/${run.runId}?timestamp=${timestamp}`}>
            <Mono>{titleForRun(run)}</Mono>
          </Link>
        </Box>
      </td>
    </tr>
  );
};

const MetadataTableContainer = styled.div`
  margin-top: -4px;
  margin-bottom: -10px;

  & tbody > tr > td {
    font-size: 13px;
  }
`;

interface PredecessorDialogProps {
  hasLineage: boolean;
  isPartitioned: boolean;
  predecessors: AssetMaterializationFragment[];
}

export const AssetPredecessorLink: React.FC<PredecessorDialogProps> = ({
  hasLineage,
  isPartitioned,
  predecessors,
}) => {
  const [open, setOpen] = React.useState(false);
  const count = predecessors.length;
  const title = () => {
    if (isPartitioned) {
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
            isPartitioned={isPartitioned}
            materializations={predecessors.map((p) => ({latest: p}))}
            shouldBucketPartitions={false}
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
