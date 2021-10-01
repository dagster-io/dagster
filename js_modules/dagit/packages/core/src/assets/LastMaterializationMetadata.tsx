import {gql} from 'graphql.macro';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {MetadataTable} from '../ui/MetadataTable';
import {Mono} from '../ui/Text';

import {AssetLineageElements} from './AssetLineageElements';
import {LatestMaterializationMetadataFragment} from './types/LatestMaterializationMetadataFragment';

export const LatestMaterializationMetadata: React.FC<{
  latest: LatestMaterializationMetadatataFragment | undefined;
  asOf: string | null;
}> = ({latest, asOf}) => {
  if (!latest) {
    return (
      <div>
        No materializations found at{' '}
        <Timestamp
          timestamp={{ms: Number(asOf)}}
          timeFormat={{showSeconds: true, showTimezone: true}}
        />
        .
      </div>
    );
  }

  const latestEvent = latest.materializationEvent;
  const latestRun = latest.runOrError.__typename === 'PipelineRun' ? latest.runOrError : null;
  const latestAssetLineage = latestEvent?.assetLineage;

  return (
    <MetadataTable
      rows={[
        {
          key: 'Run',
          value: latestRun ? (
            <div>
              <Box margin={{bottom: 4}}>
                {'Run '}
                <Link to={`/instance/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}>
                  <Mono>{titleForRun({runId: latestEvent.runId})}</Mono>
                </Link>
              </Box>
              <Box padding={{left: 8}}>
                <PipelineReference
                  showIcon
                  pipelineName={latestRun.pipelineName}
                  pipelineHrefContext="repo-unknown"
                  snapshotId={latestRun.pipelineSnapshotId}
                  mode={latestRun.mode}
                />
              </Box>
              <Group direction="row" padding={{left: 8}} spacing={8} alignItems="center">
                <IconWIP name="linear_scale" color={ColorsWIP.Gray500} />
                <Link
                  to={`/instance/runs/${latestRun.runId}?${qs.stringify({
                    selection: latestEvent.stepKey,
                    logs: `step:${latestEvent.stepKey}`,
                  })}`}
                >
                  {latestEvent.stepKey}
                </Link>
              </Group>
            </div>
          ) : (
            'No materialization events'
          ),
        },
        latest?.partition
          ? {
              key: 'Latest partition',
              value: latest ? latest.partition : 'No materialization events',
            }
          : undefined,
        {
          key: 'Timestamp',
          value: latestEvent ? (
            <Timestamp timestamp={{ms: Number(latestEvent.timestamp)}} />
          ) : (
            'No materialization events'
          ),
        },
        latestAssetLineage?.length
          ? {
              key: 'Parent assets',
              value: (
                <AssetLineageElements
                  elements={latestAssetLineage}
                  timestamp={latestEvent.timestamp}
                />
              ),
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

export const LATEST_MATERIALIZATION_METADATA_FRAGMENT = gql`
  fragment LatestMaterializationMetadataFragment on AssetMaterialization {
    partition
    runOrError {
      ... on PipelineRun {
        id
        runId
        mode
        pipelineName
        pipelineSnapshotId
      }
    }
    materializationEvent {
      runId
      timestamp
      stepKey
      stepStats {
        endTime
        startTime
      }
      materialization {
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
      assetLineage {
        assetKey {
          path
        }
        partitions
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
`;
