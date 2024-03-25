import {Box, Colors, Group, Icon, Mono, NonIdealState, Table} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetLineageElements} from './AssetLineageElements';
import {ChangedReasonsTag} from './ChangedReasons';
import {StaleReasonsTag} from './Stale';
import {isRunlessEvent} from './isRunlessEvent';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {
  AssetMaterializationFragment,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {Timestamp} from '../app/time/Timestamp';
import {LiveDataForNode, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {MetadataEntry} from '../metadata/MetadataEntry';
import {isCanonicalColumnLineageEntry} from '../metadata/TableSchema';
import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {useStepLogs} from '../runs/StepLogsDialog';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const LatestMaterializationMetadata = ({
  assetKey,
  latest,
  liveData,
  definition,
}: {
  assetKey: AssetKeyInput;
  latest: AssetObservationFragment | AssetMaterializationFragment | undefined;
  liveData: LiveDataForNode | undefined;
  definition: Pick<AssetViewDefinitionNodeFragment, 'changedReasons'>;
}) => {
  const latestRun = latest?.runOrError.__typename === 'Run' ? latest?.runOrError : null;
  const repositoryOrigin = latestRun?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);
  const latestEvent = latest;
  const latestAssetLineage =
    latestEvent?.__typename === 'MaterializationEvent' ? latestEvent?.assetLineage : [];

  const stepLogs = useStepLogs(
    latestEvent?.stepKey
      ? {runId: latestEvent.runId, stepKeys: [latestEvent.stepKey]}
      : {runId: undefined, stepKeys: []},
  );

  return (
    <>
      {stepLogs.dialog}
      {latestEvent ? (
        <MetadataTable>
          <tbody>
            {!isRunlessEvent(latestEvent) ? (
              <tr>
                <td>Run</td>
                <td>
                  {latestRun ? (
                    <div>
                      <Box
                        flex={{
                          direction: 'row',
                          justifyContent: 'space-between',
                          gap: 8,
                          alignItems: 'flex-start',
                        }}
                      >
                        <Box>
                          {'Run '}
                          <Link
                            to={`/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}
                          >
                            <Mono>{titleForRun({id: latestEvent.runId})}</Mono>
                          </Link>
                        </Box>
                        {stepLogs.button}
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
                          <Group
                            direction="row"
                            padding={{left: 8}}
                            spacing={8}
                            alignItems="center"
                          >
                            <Icon name="linear_scale" color={Colors.accentGray()} />
                            <Link to={linkToRunEvent(latestRun, latestEvent)}>
                              {latestEvent.stepKey}
                            </Link>
                          </Group>
                        </>
                      )}
                    </div>
                  ) : (
                    'No materialization events'
                  )}
                </td>
              </tr>
            ) : null}
            {latestEvent.partition ? (
              <tr>
                <td>Partition</td>
                <td>{latestEvent.partition}</td>
              </tr>
            ) : null}
            <tr>
              <td>Timestamp</td>
              <td>
                <Box flex={{gap: 8, alignItems: 'center'}}>
                  <Timestamp timestamp={{ms: Number(latestEvent.timestamp)}} />
                  {liveData && (
                    <>
                      <StaleReasonsTag assetKey={assetKey} liveData={liveData} />
                      <ChangedReasonsTag
                        changedReasons={definition.changedReasons}
                        assetKey={assetKey}
                      />
                    </>
                  )}
                </Box>
              </td>
            </tr>
            {isRunlessEvent(latestEvent) ? (
              <tr>
                <td>Description</td>
                <td style={{color: Colors.textLight()}}>
                  <Description
                    description={latestEvent.description}
                    fontSize={14}
                    maxHeight={150}
                  />
                </td>
              </tr>
            ) : null}
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
            {latestEvent.metadataEntries
              .filter((entry) => !isCanonicalColumnLineageEntry(entry))
              .map((entry) => (
                <tr key={`metadata-${entry.label}`}>
                  <td>{entry.label}</td>
                  <td>
                    <MetadataEntry
                      entry={entry}
                      expandSmallValues={true}
                      repoLocation={repoAddress?.location}
                    />
                  </td>
                </tr>
              ))}
          </tbody>
        </MetadataTable>
      ) : (
        <Box padding={{top: 16, bottom: 32}}>
          <NonIdealState
            icon="materialization"
            title="No metadata"
            description="No metadata was found for this asset."
          />
        </Box>
      )}
    </>
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
