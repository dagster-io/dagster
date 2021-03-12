import React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from 'src/app/time/Timestamp';
import {AssetLineageInfoElement} from 'src/assets/AssetLineageInfoElement';
import {AssetQuery_assetOrError_Asset_assetMaterializations} from 'src/assets/types/AssetQuery';
import {PipelineReference} from 'src/pipelines/PipelineReference';
import {MetadataEntries} from 'src/runs/MetadataEntry';
import {RunStatusTagWithStats} from 'src/runs/RunStatusTag';
import {titleForRun} from 'src/runs/RunUtils';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {FontFamily} from 'src/ui/styles';

export const AssetMaterializationTable: React.FunctionComponent<{
  isPartitioned: boolean;
  hasLineage: boolean;
  materializations: AssetQuery_assetOrError_Asset_assetMaterializations[];
}> = ({isPartitioned, hasLineage, materializations}) => {
  return (
    <Table>
      <thead>
        <tr>
          <th style={{paddingLeft: 0}}>Materialization Metadata</th>
          {isPartitioned && <th style={{minWidth: 100}}>Partition</th>}
          {hasLineage && <th style={{minWidth: 100}}>Parent Assets</th>}
          <th style={{minWidth: 150}}>Timestamp</th>
          <th style={{minWidth: 150}}>Pipeline</th>
          <th style={{width: 200}}>Run</th>
        </tr>
      </thead>
      <tbody>
        {materializations.map((m) => (
          <AssetMaterializationRow
            key={m.materializationEvent.timestamp}
            isPartitioned={isPartitioned}
            hasLineage={hasLineage}
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
  hasLineage: boolean;
}> = ({assetMaterialization, isPartitioned, hasLineage}) => {
  const run =
    assetMaterialization.runOrError.__typename === 'PipelineRun'
      ? assetMaterialization.runOrError
      : undefined;
  if (!run) {
    return <span />;
  }
  const {materialization, assetLineage, timestamp} = assetMaterialization.materializationEvent;
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
      {hasLineage && (
        <td>
          {
            <Group direction={'column'} spacing={0}>
              {assetLineage.map((lineage_info) => (
                <>
                  <AssetLineageInfoElement lineage_info={lineage_info} />
                </>
              ))}
            </Group>
          }
        </td>
      )}
      <td>
        <Timestamp timestamp={{ms: Number(timestamp)}} />
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
