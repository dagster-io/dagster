import {
  Box,
  Colors,
  Heading,
  Icon,
  MiddleTruncate,
  Mono,
  NonIdealState,
  Spinner,
  Subheading,
  Tag,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AssetCheckHistoricalEventsButton} from './AssetCheckHistoricalEventsButton';
import {AssetCheckPartitionStatus} from './AssetCheckPartitionStatus';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {useAssetCheckPartitionDetail} from './useAssetCheckPartitionDetail';
import {Timestamp} from '../../app/time/Timestamp';
import {MetadataEntries} from '../../metadata/MetadataEntry';
import {linkToRunEvent, titleForRun} from '../../runs/RunUtils';
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
      <Box padding={{horizontal: 24, bottom: 24}} style={{flex: 1}}>
        <Box padding={{vertical: 24}} border="bottom" flex={{alignItems: 'center'}}>
          <Heading>
            <MiddleTruncate text={partitionKey} />
          </Heading>
          <div style={{flex: 1}} />
          <Tag intent="none">No execution attempted</Tag>
        </Box>
        <Box padding={{top: 24}}>
          <Box style={{color: Colors.textLight(), fontSize: '14px'}}>
            This partition has not been executed for this asset check yet.
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box padding={{horizontal: 24, bottom: 24}} style={{flex: 1}}>
      <Box padding={{vertical: 24}} border="bottom" flex={{alignItems: 'center'}}>
        <Heading>
          <MiddleTruncate text={partitionKey} />
        </Heading>
        <div style={{flex: 1}} />
        {executionLoading ? (
          <Spinner purpose="body-text" />
        ) : latestExecution ? (
          <AssetCheckStatusTag execution={latestExecution} />
        ) : (
          <Tag intent="none">No execution data</Tag>
        )}
      </Box>

      <Box
        style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, minHeight: 76}}
        border="bottom"
        padding={{vertical: 16}}
      >
        {!latestExecution || !latestExecution.evaluation ? (
          <Box flex={{gap: 4, direction: 'column'}}>
            <Subheading>Latest execution</Subheading>
            <Box flex={{gap: 4}}>
              <Icon name="status" />
              None
            </Box>
          </Box>
        ) : (
          <Box flex={{gap: 4, direction: 'column'}}>
            <Subheading>Latest execution</Subheading>
            <Box flex={{gap: 4}} style={{whiteSpace: 'nowrap'}}>
              <Icon name="check_circle" />
              <Timestamp timestamp={{ms: Number(latestExecution.evaluation.timestamp)}} />
            </Box>
          </Box>
        )}

        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Run</Subheading>
          {latestExecution ? (
            <Link
              to={linkToRunEvent(
                {id: latestExecution.runId},
                {stepKey: latestExecution.stepKey, timestamp: latestExecution.timestamp},
              )}
            >
              <Mono>{titleForRun({id: latestExecution.runId})}</Mono>
            </Link>
          ) : (
            'None'
          )}
        </Box>

        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Target materialization</Subheading>
          {latestExecution?.evaluation?.targetMaterialization ? (
            <Box flex={{gap: 4}} style={{whiteSpace: 'nowrap'}}>
              <Icon name="materialization" />
              <Link to={`/runs/${latestExecution.evaluation.targetMaterialization.runId}`}>
                <Timestamp
                  timestamp={{
                    ms: Number(latestExecution.evaluation.targetMaterialization.timestamp),
                  }}
                />
              </Link>
            </Box>
          ) : (
            'None'
          )}
        </Box>

        <Box style={{textAlign: 'right'}}>
          <AssetCheckHistoricalEventsButton
            executions={executionData?.assetCheckExecutions || []}
            partitionKey={partitionKey}
            disabled={
              !executionData?.assetCheckExecutions ||
              executionData.assetCheckExecutions.length === 0
            }
          >
            {`View all historical executions (${executionData?.assetCheckExecutions?.length || 0})`}
          </AssetCheckHistoricalEventsButton>
        </Box>
      </Box>

      {latestExecution?.evaluation?.description && (
        <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
          <Subheading>Description</Subheading>
          <Box style={{color: Colors.textDefault()}}>{latestExecution.evaluation.description}</Box>
        </Box>
      )}

      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Subheading>Metadata</Subheading>
        {latestExecution?.evaluation?.metadataEntries &&
        latestExecution.evaluation.metadataEntries.length > 0 ? (
          <MetadataEntries entries={latestExecution.evaluation.metadataEntries} />
        ) : (
          <Box style={{color: Colors.textLight()}}>No metadata</Box>
        )}
      </Box>
    </Box>
  );
};
