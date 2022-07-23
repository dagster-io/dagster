import {Box, Caption, Colors, Popover, Tag} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

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

export type TagType = {
  key: string;
  value: string;
};

type TagAction = {
  label: React.ReactNode;
  onClick: (tag: TagType) => void;
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

  const tagElement = (
    <Tag intent={isDagsterTag ? 'none' : 'primary'} interactive icon={icon || undefined}>
      {displayedKey ? `${displayedKey}: ${value}` : value}
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
