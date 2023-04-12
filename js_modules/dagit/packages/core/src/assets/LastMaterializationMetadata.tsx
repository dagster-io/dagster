import {Box, Colors, Group, Icon, Mono, NonIdealState, Table} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {isHiddenAssetGroupJob, LiveDataForNode} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {MetadataEntry} from '../metadata/MetadataEntry';
import {PipelineReference} from '../pipelines/PipelineReference';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetLineageElements} from './AssetLineageElements';
import {StaleReasonsTags} from './Stale';
import {
  AssetObservationFragment,
  AssetMaterializationFragment,
} from './types/useRecentAssetEvents.types';

export const LatestMaterializationMetadata: React.FC<{
  assetKey: AssetKeyInput;
  latest: AssetObservationFragment | AssetMaterializationFragment | undefined;
  liveData: LiveDataForNode | undefined;
}> = ({assetKey, latest, liveData}) => {
  const latestRun = latest?.runOrError.__typename === 'Run' ? latest?.runOrError : null;
  const repositoryOrigin = latestRun?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  if (!latest) {
    return (
      <Box padding={{top: 16, bottom: 32}}>
        <NonIdealState
          icon="materialization"
          title="No metadata"
          description="No metadata was found for this asset."
        />
      </Box>
    );
  }

  const latestEvent = latest;
  const latestAssetLineage =
    latestEvent.__typename === 'MaterializationEvent' ? latestEvent?.assetLineage : [];

  return (
    <MetadataTable>
      <tbody>
        <tr>
          <td>Run</td>
          <td>
            {latestRun ? (
              <div>
                <Box>
                  {'Run '}
                  <Link to={`/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}>
                    <Mono>{titleForRun({id: latestEvent.runId})}</Mono>
                  </Link>
                </Box>
                {!isHiddenAssetGroupJob(latestRun.pipelineName) && (
                  <>
                    <Box padding={{left: 8, top: 4}}>
                      <PipelineReference
                        showIcon
                        pipelineName={latestRun.pipelineName}
                        pipelineHrefContext={repoAddress || 'repo-unknown'}
                        snapshotId={latestRun.pipelineSnapshotId}
                        isJob={isThisThingAJob(repo, latestRun.pipelineName)}
                      />
                    </Box>
                    <Group direction="row" padding={{left: 8}} spacing={8} alignItems="center">
                      <Icon name="linear_scale" color={Colors.Gray400} />
                      <Link to={linkToRunEvent(latestRun, latestEvent)}>{latestEvent.stepKey}</Link>
                    </Group>
                  </>
                )}
              </div>
            ) : (
              'No materialization events'
            )}
          </td>
          <td />
        </tr>
        {latest?.partition ? (
          <tr>
            <td>Partition</td>
            <td>{latest ? latest.partition : 'No materialization events'}</td>
            <td />
          </tr>
        ) : null}
        <tr>
          <td>Timestamp</td>
          <td>
            <Box flex={{gap: 8, alignItems: 'center'}}>
              {latestEvent ? (
                <Timestamp timestamp={{ms: Number(latestEvent.timestamp)}} />
              ) : (
                'No materialization events'
              )}
              {liveData && (
                <StaleReasonsTags assetKey={assetKey} liveData={liveData} include="all" />
              )}
            </Box>
          </td>
          <td />
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
            <td />
          </tr>
        ) : null}
        {latestEvent?.metadataEntries.map((entry) => (
          <tr key={`metadata-${entry.label}`}>
            <td>{entry.label}</td>
            <td>
              <MetadataEntry
                entry={entry}
                expandSmallValues={true}
                repoLocation={repoAddress?.location}
              />
            </td>
            <td>{entry.description}</td>
          </tr>
        ))}
      </tbody>
    </MetadataTable>
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
