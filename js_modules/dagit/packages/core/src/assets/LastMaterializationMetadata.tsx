import {gql} from 'graphql.macro';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {PipelineReference} from '../pipelines/PipelineReference';
import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';
import {Table} from '../ui/Table';
import {Mono} from '../ui/Text';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetLineageElements} from './AssetLineageElements';
import {LatestMaterializationMetadataFragment} from './types/LatestMaterializationMetadataFragment';

export const LatestMaterializationMetadata: React.FC<{
  latest: LatestMaterializationMetadataFragment | undefined;
  asOf: string | null;
}> = ({latest, asOf}) => {
  const latestRun = latest?.runOrError.__typename === 'PipelineRun' ? latest?.runOrError : null;
  const repositoryOrigin = latestRun?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  if (!latest) {
    if (!asOf) {
      return (
        <Box padding={{top: 16, bottom: 32}}>
          <NonIdealState
            icon="asset"
            title="No materializations"
            description="No materializations were found for this asset."
          />
        </Box>
      );
    }

    return (
      <Box padding={{top: 16, bottom: 32}}>
        <NonIdealState
          icon="asset"
          title="No materializations"
          description={
            <div>
              No materializations found at{' '}
              <Timestamp
                timestamp={{ms: Number(asOf)}}
                timeFormat={{showSeconds: true, showTimezone: true}}
              />
              .
            </div>
          }
        />
      </Box>
    );
  }

  const latestEvent = latest?.materializationEvent;
  const latestAssetLineage = latestEvent?.assetLineage;

  return (
    <Box padding={{bottom: 16}}>
      <MetadataTable>
        <tbody>
          <tr>
            <td>Run</td>
            <td>
              {latestRun ? (
                <div>
                  <Box margin={{bottom: 4}}>
                    {'Run '}
                    <Link
                      to={`/instance/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}
                    >
                      <Mono>{titleForRun({runId: latestEvent.runId})}</Mono>
                    </Link>
                  </Box>
                  <Box padding={{left: 8}}>
                    <PipelineReference
                      showIcon
                      pipelineName={latestRun.pipelineName}
                      pipelineHrefContext={repoAddress || 'repo-unknown'}
                      snapshotId={latestRun.pipelineSnapshotId}
                      isJob={isThisThingAJob(repo, latestRun.pipelineName)}
                    />
                  </Box>
                  <Group direction="row" padding={{left: 8}} spacing={8} alignItems="center">
                    <IconWIP name="linear_scale" color={ColorsWIP.Gray400} />
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
              )}
            </td>
          </tr>
          {latest?.partition ? (
            <tr>
              <td>Latest partition</td>
              <td>{latest ? latest.partition : 'No materialization events'}</td>
            </tr>
          ) : null}
          <tr>
            <td>Timestamp</td>
            <td>
              {latestEvent ? (
                <Timestamp timestamp={{ms: Number(latestEvent.timestamp)}} />
              ) : (
                'No materialization events'
              )}
            </td>
          </tr>
          {latestAssetLineage?.length ? (
            <tr>
              <td>Parent assets</td>
              <td>
                <AssetLineageElements
                  elements={latestAssetLineage}
                  timestamp={latestEvent.timestamp}
                />
              </td>
            </tr>
          ) : null}
          {latestEvent?.materialization.metadataEntries.map((entry) => (
            <tr key={`metadata-${entry.label}`}>
              <td>{entry.label}</td>
              <td>
                <MetadataEntry entry={entry} expandSmallValues={true} />
              </td>
            </tr>
          ))}
        </tbody>
      </MetadataTable>
    </Box>
  );
};

const MetadataTable = styled(Table)`
  td:first-child {
    white-space: nowrap;
    width: 1px;
    max-width: 400px;
    word-break: break-word;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`;

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
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
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
