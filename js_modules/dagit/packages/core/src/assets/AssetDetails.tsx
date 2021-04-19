import {useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntry} from '../runs/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {MetadataTable} from '../ui/MetadataTable';
import {Spinner} from '../ui/Spinner';
import {Subheading} from '../ui/Text';
import {FontFamily} from '../ui/styles';

import {AssetLineageElements} from './AssetLineageElements';
import {ASSET_QUERY} from './queries';
import {AssetKey} from './types';
import {AssetQuery, AssetQueryVariables} from './types/AssetQuery';

export const AssetDetails: React.FC<{assetKey: AssetKey}> = ({assetKey}) => {
  const {data, loading} = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}, limit: 1},
  });

  const content = () => {
    if (loading) {
      return (
        <Box padding={{vertical: 20}}>
          <Spinner purpose="section" />
        </Box>
      );
    }

    const assetOrError = data?.assetOrError;

    if (!assetOrError || assetOrError.__typename !== 'Asset') {
      return null;
    }

    const latest = assetOrError.assetMaterializations[0];
    const latestEvent = latest && latest.materializationEvent;
    const latestRun =
      latest && latest.runOrError.__typename === 'PipelineRun' ? latest.runOrError : null;
    const latestAssetLineage = latestEvent && latestEvent.assetLineage;

    return (
      <MetadataTable
        rows={[
          {
            key: 'Latest materialization from',
            value: latestRun ? (
              <div>
                <div>
                  {'Run '}
                  <Link
                    style={{fontFamily: FontFamily.monospace}}
                    to={`/instance/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}
                  >
                    {titleForRun({runId: latestEvent.runId})}
                  </Link>
                </div>
                <div style={{paddingLeft: 10, paddingTop: 4}}>
                  <Icon
                    icon="diagram-tree"
                    color={Colors.GRAY2}
                    iconSize={12}
                    style={{position: 'relative', top: -2, paddingRight: 5}}
                  />
                  <PipelineReference
                    pipelineName={latestRun.pipelineName}
                    pipelineHrefContext="repo-unknown"
                    snapshotId={latestRun.pipelineSnapshotId}
                    mode={latestRun.mode}
                  />
                </div>
                <div style={{paddingLeft: 10, paddingTop: 4}}>
                  <Icon
                    icon="git-commit"
                    color={Colors.GRAY2}
                    iconSize={12}
                    style={{position: 'relative', top: -2, paddingRight: 5}}
                  />
                  <Link
                    to={`/instance/runs/${latestRun.runId}?${qs.stringify({
                      selection: latest.materializationEvent.stepKey,
                      logs: `step:${latest.materializationEvent.stepKey}`,
                    })}`}
                  >
                    {latest.materializationEvent.stepKey}
                  </Link>
                </div>
              </div>
            ) : (
              'No materialization events'
            ),
          },
          latest.partition
            ? {
                key: 'Latest partition',
                value: latest ? latest.partition : 'No materialization events',
              }
            : undefined,
          {
            key: 'Latest timestamp',
            value: latestEvent ? (
              <Timestamp timestamp={{ms: Number(latestEvent.timestamp)}} />
            ) : (
              'No materialization events'
            ),
          },
          latestAssetLineage.length > 0
            ? {
                key: 'Latest parent assets',
                value: <AssetLineageElements elements={latestAssetLineage} />,
              }
            : undefined,
          ...latestEvent?.materialization.metadataEntries.map((entry) => ({
            key: entry.label,
            value: <MetadataEntry entry={entry} expandSmallValues={true} />,
          })),
        ].filter(Boolean)}
      />
    );
  };

  const isPartitioned = !!(
    data?.assetOrError?.__typename === 'Asset' &&
    data.assetOrError.assetMaterializations[0].partition
  );

  return (
    <Group direction="column" spacing={8}>
      <Subheading>{isPartitioned ? 'Latest Materialized Partition' : 'Details'}</Subheading>
      {content()}
    </Group>
  );
};
