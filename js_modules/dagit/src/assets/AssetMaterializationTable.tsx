import React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from 'src/app/time/Timestamp';
import {AssetQuery_assetOrError_Asset_assetMaterializations} from 'src/assets/types/AssetQuery';
import {PipelineSnapshotLink} from 'src/pipelines/PipelinePathUtils';
import {MetadataEntries} from 'src/runs/MetadataEntry';
import {RunStatusTagWithStats} from 'src/runs/RunStatusTag';
import {titleForRun} from 'src/runs/RunUtils';
import {Table} from 'src/ui/Table';
import {FontFamily} from 'src/ui/styles';

export const AssetMaterializationTable: React.FunctionComponent<{
  isPartitioned: boolean;
  materializations: AssetQuery_assetOrError_Asset_assetMaterializations[];
}> = ({isPartitioned, materializations}) => {
  return (
    <Table>
      <thead>
        <tr>
          <th style={{paddingLeft: 0}}>Materialization Metadata</th>
          {isPartitioned && <th style={{width: 100}}>Partition</th>}
          <th style={{width: 150}}>Timestamp</th>
          <th style={{width: 150, maxWidth: 250}}>Pipeline</th>
          <th style={{width: 200}}>Run</th>
        </tr>
      </thead>
      <tbody>
        {materializations.map((m) => (
          <AssetMaterializationRow
            key={m.materializationEvent.timestamp}
            isPartitioned={isPartitioned}
            assetMaterialization={m}
          />
        ))}
      </tbody>
    </Table>
  );
};

const AssetMaterializationRow: React.FunctionComponent<{
  assetMaterialization: AssetQuery_assetOrError_Asset_assetMaterializations;
  isPartitioned: boolean;
}> = ({assetMaterialization, isPartitioned}) => {
  const run =
    assetMaterialization.runOrError.__typename === 'PipelineRun'
      ? assetMaterialization.runOrError
      : undefined;
  if (!run) {
    return <span />;
  }
  const {materialization, timestamp} = assetMaterialization.materializationEvent;
  const metadataEntries = materialization.metadataEntries;

  return (
    <tr>
      <td style={{fontSize: 12, padding: 5, paddingTop: 3}}>
        {materialization.description ? (
          <div style={{fontSize: '0.8rem', marginTop: 10}}>{materialization.description}</div>
        ) : null}
        {metadataEntries && metadataEntries.length ? (
          <MetadataEntries entries={metadataEntries} />
        ) : null}
      </td>
      {isPartitioned && <td>{assetMaterialization.partition}</td>}
      <td>
        <Timestamp ms={Number(timestamp)} />
      </td>
      <td>
        {run.pipelineName}
        <PipelineSnapshotLink
          snapshotId={run.pipelineSnapshotId || ''}
          pipelineName={run.pipelineName}
        />
      </td>
      <td>
        <Link
          style={{marginRight: 5, fontFamily: FontFamily.monospace}}
          to={`/instance/runs/${run.runId}?timestamp=${timestamp}`}
        >
          {titleForRun(run)}
        </Link>
        <RunStatusTagWithStats status={run.status} runId={run.runId} />
      </td>
    </tr>
  );
};
