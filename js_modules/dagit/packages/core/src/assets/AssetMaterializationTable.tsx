import {Button, Classes, Colors, Dialog} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntries} from '../runs/MetadataEntry';
import {RunStatusTagWithStats} from '../runs/RunStatusTag';
import {titleForRun} from '../runs/RunUtils';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';
import {Mono} from '../ui/Text';

import {AssetLineageElements} from './AssetLineageElements';
import {AssetQuery_assetOrError_Asset_assetMaterializations as Materialization} from './types/AssetQuery';
import {HistoricalMaterialization} from './useMaterializationBuckets';

export const AssetMaterializationTable: React.FC<{
  isPartitioned: boolean;
  hasLineage: boolean;
  materializations: HistoricalMaterialization[];
  shouldBucketPartitions?: boolean;
}> = ({isPartitioned, hasLineage, materializations, shouldBucketPartitions = true}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
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
          <th style={{paddingLeft: 0}}>Materialization Metadata</th>
          {hasLineage && <th style={{minWidth: 100}}>Parent Materializations</th>}
          <th style={{minWidth: 150}}>Timestamp</th>
          <th style={{minWidth: 150}}>{flagPipelineModeTuples ? 'Job' : 'Pipeline'}</th>
          <th style={{width: 200}}>Run</th>
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
  if (!run) {
    return <span />;
  }
  const {materialization, assetLineage, timestamp} = latest.materializationEvent;
  const metadataEntries = materialization.metadataEntries;

  return (
    <tr>
      {isPartitioned && (
        <td>{latest.partition || <span style={{color: Colors.GRAY3}}>None</span>}</td>
      )}
      <td style={{fontSize: 12, padding: '4px 12px 0 0'}}>
        {materialization.description ? (
          <div style={{fontSize: '0.8rem', marginTop: 10}}>{materialization.description}</div>
        ) : null}
        {metadataEntries && metadataEntries.length ? (
          <MetadataEntries entries={metadataEntries} />
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
          pipelineHrefContext="repo-unknown"
          snapshotId={run.pipelineSnapshotId}
          mode={run.mode}
        />
      </td>
      <td>
        <Group direction="row" spacing={4}>
          <Link to={`/instance/runs/${run.runId}?timestamp=${timestamp}`}>
            <Mono>{titleForRun(run)}</Mono>
          </Link>
          <RunStatusTagWithStats status={run.status} runId={run.runId} />
        </Group>
      </td>
    </tr>
  );
};

interface PredecessorDialogProps {
  hasLineage: boolean;
  isPartitioned: boolean;
  predecessors: Materialization[];
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
      <Dialog
        isOpen={open}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setOpen(false)}
        style={{width: '80%', minWidth: '800px'}}
        title={title()}
      >
        <div className={Classes.DIALOG_BODY}>
          <AssetMaterializationTable
            hasLineage={hasLineage}
            isPartitioned={isPartitioned}
            materializations={predecessors.map((p) => ({latest: p}))}
            shouldBucketPartitions={false}
          />
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button intent="primary" onClick={() => setOpen(false)}>
              OK
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};
