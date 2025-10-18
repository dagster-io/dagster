import {Box, Heading, NonIdealState, Spinner, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AssetCheckPartitionStatus} from './AssetCheckPartitionStatus';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {useAssetCheckPartitionDetail} from './useAssetCheckPartitionDetail';
import {MetadataEntries} from '../../metadata/MetadataEntry';
import {linkToRunEvent} from '../../runs/RunUtils';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {AssetKey} from '../types';

interface AssetCheckPartitionDetailProps {
  assetKey: AssetKey;
  checkName: string;
  partitionKey: string;
}

export const AssetCheckPartitionDetail = ({
  assetKey,
  checkName,
  partitionKey,
}: AssetCheckPartitionDetailProps) => {
  const {data: executionData, loading: executionLoading} = useAssetCheckPartitionDetail(
    assetKey,
    checkName,
    partitionKey,
  );

  const latestExecution = useMemo(() => {
    if (!executionData?.assetCheckExecutions?.length) {
      return null;
    }

    return executionData.assetCheckExecutions[0];
  }, [executionData]);

  const partitionStatus = useMemo(() => {
    if (!latestExecution) {
      return AssetCheckPartitionStatus.MISSING;
    }
    return latestExecution.status;
  }, [latestExecution]);

  if (executionLoading || !executionData) {
    return (
      <Box
        flex={{direction: 'column', justifyContent: 'center', alignItems: 'center'}}
        style={{height: '100%'}}
      >
        <Spinner purpose="section" />
      </Box>
    );
  }

  if (!partitionStatus) {
    return (
      <Box padding={24}>
        <NonIdealState
          title="Partition not found"
          description={`No data available for partition "${partitionKey}"`}
          icon="partition"
        />
      </Box>
    );
  }

  const primaryStatus = partitionStatus;

  // Handle missing status with a blank state
  if (primaryStatus === AssetCheckPartitionStatus.MISSING) {
    return (
      <Box padding={24}>
        <Box flex={{direction: 'column', gap: 16}}>
          <Heading>{partitionKey}</Heading>

          <Box flex={{direction: 'column', gap: 12}}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <strong>Status:</strong>
              <Tag intent="none">No execution attempted</Tag>
            </Box>

            <Box flex={{direction: 'column', gap: 8}}>
              <Box style={{color: '#666', fontSize: '14px'}}>
                This partition has not been executed for this asset check yet.
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box padding={24}>
      <Box flex={{direction: 'column', gap: 16}}>
        <Heading>{partitionKey}</Heading>

        <Box flex={{direction: 'column', gap: 12}}>
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <strong>Status:</strong>
            {latestExecution ? (
              <AssetCheckStatusTag execution={latestExecution} />
            ) : (
              <Tag intent="none">No execution data</Tag>
            )}
          </Box>

          {executionLoading ? (
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <Spinner purpose="body-text" />
              <span>Loading execution details...</span>
            </Box>
          ) : latestExecution ? (
            <Box flex={{direction: 'column', gap: 12}}>
              {/* Execution timestamp */}
              {latestExecution.evaluation?.timestamp && (
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                  <strong>Executed:</strong>
                  <Link
                    to={linkToRunEvent(
                      {id: latestExecution.runId},
                      {stepKey: latestExecution.stepKey, timestamp: latestExecution.timestamp},
                    )}
                  >
                    <TimestampDisplay timestamp={latestExecution.evaluation.timestamp} />
                  </Link>
                </Box>
              )}

              {/* Target materialization */}
              {latestExecution.evaluation?.targetMaterialization && (
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                  <strong>Target materialization:</strong>
                  <Link to={`/runs/${latestExecution.evaluation.targetMaterialization.runId}`}>
                    <TimestampDisplay
                      timestamp={latestExecution.evaluation.targetMaterialization.timestamp}
                    />
                  </Link>
                </Box>
              )}

              {/* Description */}
              {latestExecution.evaluation?.description && (
                <Box flex={{direction: 'column', gap: 4}}>
                  <strong>Description:</strong>
                  <Box style={{color: '#666'}}>{latestExecution.evaluation.description}</Box>
                </Box>
              )}

              {/* Metadata */}
              {latestExecution.evaluation?.metadataEntries &&
                latestExecution.evaluation.metadataEntries.length > 0 && (
                  <Box flex={{direction: 'column', gap: 4}}>
                    <strong>Metadata:</strong>
                    <MetadataEntries entries={latestExecution.evaluation.metadataEntries} />
                  </Box>
                )}
            </Box>
          ) : (
            <Box style={{color: '#666', fontSize: '14px'}}>
              No execution data available for this partition.
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};
