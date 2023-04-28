import {Box, Caption, Colors, Popover, Tag} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

export enum DagsterTag {
  Automaterialize = 'dagster/auto_materialize',
  Namespace = 'dagster/',
  Backfill = 'dagster/backfill',
  CreatedBy = 'dagster/created_by',
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
  AssetPartitionRangeStart = 'dagster/asset_partition_range_start',
  AssetPartitionRangeEnd = 'dagster/asset_partition_range_end',
  AssetEventDataVersion = 'dagster/data_version',
  AssetEventDataVersionDeprecated = 'dagster/logical_version',
  AssetEventCodeVersion = 'dagster/code_version',
  SnapshotID = 'dagster/snapshot_id', // This only exists on the client, not the server.
  User = 'user',

  // Hidden tags (using ".dagster" HIDDEN_TAG_PREFIX)
  RepositoryLabelTag = '.dagster/repository',
}

export type TagType = {
  key: string;
  value: string;
  link?: string;
};

export type TagAction = {
  label: React.ReactNode;
  onClick: (tag: TagType) => any;
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

  const icon = React.useMemo(() => {
    switch (key) {
      case DagsterTag.ScheduleName:
        return 'schedule';
      case DagsterTag.SensorName:
        return 'sensors';
      case DagsterTag.Backfill:
        return 'settings_backup_restore';
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
    tag.link ? <Link to={tag.link}>{children}</Link> : <>{children}</>;

  const tagElement = (
    <Tag intent={isDagsterTag ? 'none' : 'primary'} interactive icon={icon || undefined}>
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
      <Popover
        content={<TagActions actions={actions} tag={tag} />}
        hoverOpenDelay={100}
        hoverCloseDelay={100}
        placement="top"
        interactionKind="hover"
      >
        {tagElement}
      </Popover>
    );
  }

  return tagElement;
};

const TagActions = ({tag, actions}: {tag: TagType; actions: TagAction[]}) => (
  <ActionContainer background={Colors.Gray900} flex={{direction: 'row'}}>
    {actions.map(({label, onClick}, ii) => (
      <TagButton key={ii} onClick={() => onClick(tag)}>
        <Caption>{label}</Caption>
      </TagButton>
    ))}
  </ActionContainer>
);

const ActionContainer = styled(Box)`
  border-radius: 8px;
  overflow: hidden;
`;

const TagButton = styled.button`
  border: none;
  background: ${Colors.Dark};
  color: ${Colors.Gray100};
  cursor: pointer;
  padding: 8px 12px;
  text-align: left;

  :not(:last-child) {
    box-shadow: -1px 0 0 inset ${Colors.Gray600};
  }

  :focus {
    outline: none;
  }

  :hover {
    background-color: ${Colors.Gray800};
    color: ${Colors.White};
  }
`;
