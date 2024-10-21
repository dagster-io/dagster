import {IconName, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TagAction, TagActionsPopover} from '../ui/TagActions';

export enum DagsterTag {
  Automaterialize = 'dagster/auto_materialize',
  AutoObserve = 'dagster/auto_observe',
  Namespace = 'dagster/',
  Backfill = 'dagster/backfill',
  CreatedBy = 'dagster/created_by',
  ComputeKind = 'dagster/compute_kind',
  SolidSelection = 'dagster/solid_selection',
  OpSelection = 'dagster/op_selection',
  StepSelection = 'dagster/step_selection',
  PartitionSet = 'dagster/partition_set',
  Partition = 'dagster/partition',
  IsResumeRetry = 'dagster/is_resume_retry',
  PresetName = 'dagster/preset_name',
  ParentRunId = 'dagster/parent_run_id',
  RootRunId = 'dagster/root_run_id',
  ScheduleName = 'dagster/schedule_name',
  SensorName = 'dagster/sensor_name',
  StorageKind = 'dagster/storage_kind',
  TickId = 'dagster/tick',
  AssetPartitionRangeStart = 'dagster/asset_partition_range_start',
  AssetPartitionRangeEnd = 'dagster/asset_partition_range_end',
  AssetEventDataVersion = 'dagster/data_version',
  AssetEventDataVersionDeprecated = 'dagster/logical_version',
  AssetEventCodeVersion = 'dagster/code_version',
  AssetEvaluationID = 'dagster/asset_evaluation_id',
  SnapshotID = 'dagster/snapshot_id', // This only exists on the client, not the server.
  ReportingUser = 'dagster/reporting_user',
  User = 'user',

  // Hidden tags (using ".dagster" HIDDEN_TAG_PREFIX)
  RepositoryLabelTag = '.dagster/repository',
}

export type TagType = {
  key: string;
  value: string;
  link?: string;
  pinned?: boolean;
  originalKey?: string;
};

interface IRunTagProps {
  tag: TagType;
  actions?: TagAction[];
}

export const RunTag = ({tag, actions}: IRunTagProps) => {
  const {key, value} = tag;
  const isDagsterTag = key.startsWith(DagsterTag.Namespace);

  const displayedKey = React.useMemo(() => {
    if (isDagsterTag) {
      switch (key) {
        case DagsterTag.Backfill:
          return 'Backfill';
        case DagsterTag.ScheduleName:
        case DagsterTag.SensorName:
          return null;
        case DagsterTag.SnapshotID:
          return 'Snapshot';
        default:
          return key.slice(DagsterTag.Namespace.length);
      }
    }
    return key;
  }, [isDagsterTag, key]);

  const icon = React.useMemo((): IconName | null => {
    switch (key) {
      case DagsterTag.ScheduleName:
        return 'schedule';
      case DagsterTag.SensorName:
        return 'sensors';
      case DagsterTag.Backfill:
        return 'settings_backup_restore';
      case DagsterTag.Partition:
        return 'partition';
      default:
        return null;
    }
  }, [key]);

  const displayValue = React.useMemo(() => {
    switch (key) {
      case DagsterTag.SnapshotID:
        return value.slice(0, 8);
      default:
        return value;
    }
  }, [key, value]);

  const ValueWrapper = ({children}: {children: React.ReactNode}) =>
    tag.link ? <Link to={tag.link}>{children}</Link> : <span>{children}</span>;

  const tooltipValue = displayedKey ? `${displayedKey}: ${displayValue}` : displayValue;

  const tagElement = (
    <Tag
      intent={isDagsterTag ? 'none' : 'primary'}
      interactive
      icon={icon || undefined}
      tooltipText={tooltipValue}
    >
      {displayedKey ? (
        <span>
          {displayedKey}: <ValueWrapper>{displayValue}</ValueWrapper>
        </span>
      ) : (
        <ValueWrapper>{displayValue}</ValueWrapper>
      )}
    </Tag>
  );

  if (actions?.length) {
    return (
      <TagActionsPopover actions={actions} data={tag}>
        {tagElement}
      </TagActionsPopover>
    );
  }

  return tagElement;
};
