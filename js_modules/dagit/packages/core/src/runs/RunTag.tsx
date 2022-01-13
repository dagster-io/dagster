import {Tag, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

export enum DagsterTag {
  Namespace = 'dagster/',
  Backfill = 'dagster/backfill',
  SolidSelection = 'dagster/solid_selection',
  StepSelection = 'dagster/step_selection',
  PartitionSet = 'dagster/partition_set',
  Partition = 'dagster/partition',
  IsResumeRetry = 'dagster/is_resume_retry',
  PresetName = 'dagster/preset_name',
  ParentRunId = 'dagster/parent_run_id',
  RootRunId = 'dagster/root_run_id',
  ScheduleName = 'dagster/schedule_name',
  SensorName = 'dagster/sensor_name',
}

interface IRunTagProps {
  tag: {
    key: string;
    value: string;
  };
  onClick?: (tag: {key: string; value: string}) => void;
}

export const RunTag = ({tag, onClick}: IRunTagProps) => {
  const isDagsterTag = tag.key.startsWith(DagsterTag.Namespace);
  const displayTag = isDagsterTag
    ? {key: tag.key.substr(DagsterTag.Namespace.length), value: tag.value}
    : tag;

  const onTagClick = () => {
    onClick && onClick(tag);
  };

  if (isDagsterTag) {
    return (
      <Tooltip content={`${tag.key}=${tag.value}`} targetTagName="div" placement="top">
        <Tag isDagsterTag={isDagsterTag} onClick={onTagClick} tag={displayTag} />
      </Tooltip>
    );
  }

  return <Tag isDagsterTag={isDagsterTag} onClick={onTagClick} tag={displayTag} />;
};
