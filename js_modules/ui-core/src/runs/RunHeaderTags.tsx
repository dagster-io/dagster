import {Box, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {RunAssetCheckTags} from './RunAssetCheckTags';
import {RunAssetTags} from './RunAssetTags';
import {RunStatusTag} from './RunStatusTag';
import {DagsterTag, RunTag} from './RunTag';
import {RunTimingTags} from './RunTimingTags';
import {TickTagForRun} from './TickTagForRun';
import {RunPageFragment} from './types/RunFragments.types';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {AutomaterializeTagWithEvaluation} from '../assets/AutomaterializeTagWithEvaluation';
import {InstigationSelector} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RepoAddress} from '../workspace/types';

interface Props {
  run: RunPageFragment;
  repoAddress: RepoAddress | null;
  isJob: boolean;
  loading: boolean;
}

/** Status, target, instigator, partition, asset and timing tags shown for a run. */
export const RunHeaderTags = ({run, repoAddress, isJob, loading}: Props) => {
  const automaterializeTag = useMemo(
    () => run.tags.find((tag) => tag.key === DagsterTag.AssetEvaluationID) || null,
    [run],
  );

  const tickDetails = useMemo(() => {
    if (repoAddress) {
      const tags = run.tags || [];
      const tickTag = tags.find((tag) => tag.key === DagsterTag.TickId);

      if (tickTag) {
        const scheduleOrSensor = tags.find(
          (tag) => tag.key === DagsterTag.ScheduleName || tag.key === DagsterTag.SensorName,
        );
        if (scheduleOrSensor) {
          const instigationSelector: InstigationSelector = {
            name: scheduleOrSensor.value,
            repositoryName: repoAddress.name,
            repositoryLocationName: repoAddress.location,
          };
          return {
            tickId: tickTag.value,
            instigationType: scheduleOrSensor.key as
              | DagsterTag.ScheduleName
              | DagsterTag.SensorName,
            instigationSelector,
          };
        }
      }
    }

    return null;
  }, [run, repoAddress]);

  const partitionTag = run.tags.find((tag) => tag.key === DagsterTag.Partition);

  return (
    <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 12, wrap: 'wrap'}}>
      <RunStatusTag status={run.status} />
      {!isHiddenAssetGroupJob(run.pipelineName) ? (
        <Tag icon="run">
          Run of{' '}
          <PipelineReference
            pipelineName={run.pipelineName}
            pipelineHrefContext={repoAddress || 'repo-unknown'}
            snapshotId={run.pipelineSnapshotId}
            size="small"
            isJob={isJob}
          />
        </Tag>
      ) : null}
      {tickDetails ? (
        <TickTagForRun
          instigationSelector={tickDetails.instigationSelector}
          instigationType={tickDetails.instigationType}
          tickId={tickDetails.tickId}
        />
      ) : null}
      {partitionTag && <RunTag tag={partitionTag} />}
      <RunAssetTags run={run} />
      <RunAssetCheckTags run={run} />
      <RunTimingTags run={run} loading={loading} />
      {automaterializeTag && run.assetSelection?.length ? (
        <AutomaterializeTagWithEvaluation
          assetKeys={run.assetSelection}
          evaluationId={automaterializeTag.value}
        />
      ) : null}
    </Box>
  );
};
