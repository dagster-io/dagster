import {Box, Button, Icon, Menu, MenuItem, Popover, Tag} from '@dagster-io/ui-components';
import {useState} from 'react';

import {DagsterTag} from './RunTag';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTableEntryFragment.types';

type LaunchType =
  | {type: 'manual'; user: string}
  | {type: 'schedule'; name: string}
  | {type: 'sensor'; name: string}
  | {type: 'automation'}
  | {type: 'backfill-launched'; backfillId: string; user: string};

const formatTimeAgo = (timestampSeconds: number): string => {
  const now = Date.now() / 1000;
  const diffSeconds = Math.floor(now - timestampSeconds);

  if (diffSeconds < 60) {
    return `${diffSeconds} s ago`;
  }

  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hr${diffHours !== 1 ? 's' : ''} ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  }

  const diffWeeks = Math.floor(diffDays / 7);
  if (diffWeeks < 4) {
    return `${diffWeeks} wk${diffWeeks !== 1 ? 's' : ''} ago`;
  }

  const diffMonths = Math.floor(diffDays / 30);
  if (diffMonths < 12) {
    return `${diffMonths} mo${diffMonths !== 1 ? 's' : ''} ago`;
  }

  const diffYears = Math.floor(diffDays / 365);
  return `${diffYears} yr${diffYears !== 1 ? 's' : ''} ago`;
};

const detectLaunchType = (entry: RunsFeedTableEntryFragment): LaunchType => {
  const tags = entry.tags || [];
  const tagMap = tags.reduce(
    (acc, tag) => ({...acc, [tag.key]: tag.value}),
    {} as Record<string, string>,
  );

  // Check for declarative automation
  if (
    tagMap[DagsterTag.Automaterialize] === 'true' ||
    tagMap[DagsterTag.AutomationCondition] === 'true'
  ) {
    return {type: 'automation'};
  }

  // Check for schedule
  if (tagMap[DagsterTag.ScheduleName]) {
    return {type: 'schedule', name: tagMap[DagsterTag.ScheduleName]};
  }

  // Check for sensor (but not automation condition sensor)
  if (
    tagMap[DagsterTag.SensorName] &&
    tagMap[DagsterTag.SensorName] !== 'default_automation_condition_sensor'
  ) {
    return {type: 'sensor', name: tagMap[DagsterTag.SensorName]};
  }

  // Check for backfill-launched run (has both backfill ID and user)
  if (tagMap[DagsterTag.Backfill] && tagMap[DagsterTag.User]) {
    return {
      type: 'backfill-launched',
      backfillId: tagMap[DagsterTag.Backfill],
      user: tagMap[DagsterTag.User],
    };
  }

  // Check for manual user run (user tag only, no backfill)
  if (tagMap[DagsterTag.User]) {
    return {type: 'manual', user: tagMap[DagsterTag.User]};
  }

  // Default to manual
  return {type: 'manual', user: 'Unknown'};
};

const LaunchedByCell = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  const launchType = detectLaunchType(entry);

  switch (launchType.type) {
    case 'manual':
      return <Tag icon="account_circle">{launchType.user}</Tag>;
    case 'schedule':
      return <Tag icon="schedule">{launchType.name}</Tag>;
    case 'sensor':
      return <Tag icon="sensors">{launchType.name}</Tag>;
    case 'automation':
      return <Tag icon="automation_condition">Declarative automation</Tag>;
    case 'backfill-launched':
      return <Tag icon="settings_backup_restore">Backfill ({launchType.backfillId})</Tag>;
    default:
      return <Tag icon="account_circle">Manual</Tag>;
  }
};

const CreatedAtCell = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  const createdAtText = formatTimeAgo(entry.creationTime);
  return <Box style={{color: '#64748b', fontSize: '14px'}}>{createdAtText}</Box>;
};

const TagsCell = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  const [isOpen, setIsOpen] = useState(false);
  const tags = entry.tags || [];

  const copyAllTags = () => {
    const tagText = tags.map((tag) => `${tag.key}: ${tag.value}`).join('\n');
    navigator.clipboard.writeText(tagText);
  };

  const copyTag = (key: string, value: string) => {
    navigator.clipboard.writeText(`${key}: ${value}`);
  };

  const runIdShort = entry.id.slice(0, 8);

  return (
    <Popover
      isOpen={isOpen}
      onInteraction={setIsOpen}
      placement="bottom-end"
      content={
        <Box style={{minWidth: '320px', padding: '12px'}}>
          {/* Header */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px',
              paddingBottom: '8px',
              borderBottom: '1px solid #e1e5e9',
            }}
          >
            <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <Icon name="tag" size={16} />
              <span style={{fontWeight: 500}}>Tags</span>
            </Box>
            <Box style={{color: '#64748b', fontSize: '12px'}}>#{runIdShort}</Box>
          </Box>

          {/* Tags List */}
          <Box style={{display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '12px'}}>
            {tags.map((tag, index) => (
              <Box
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '4px 0',
                }}
              >
                <Box style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
                  <Box style={{fontWeight: 500, color: '#374151'}}>{tag.key}:</Box>
                  <Box style={{color: '#6b7280', marginLeft: '12px'}}>{tag.value}</Box>
                </Box>
                <Popover
                  content={
                    <Menu>
                      <MenuItem
                        text="Copy tag"
                        onClick={() => copyTag(tag.key, tag.value)}
                        icon="copy"
                      />
                    </Menu>
                  }
                  placement="left"
                >
                  <Button
                    icon="more_horiz"
                    style={{marginLeft: '8px', minWidth: 'auto', padding: '2px'}}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popover>
              </Box>
            ))}
          </Box>

          {/* Copy All Button */}
          <Button onClick={copyAllTags} style={{width: '100%'}} intent="none">
            Copy all
          </Button>
        </Box>
      }
    >
      <Button icon="tag" style={{minWidth: 'auto', padding: '4px'}} />
    </Popover>
  );
};

export const RunsFeedRow = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px 40px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '1px solid #e1e5e9',
        alignItems: 'center',
      }}
    >
      <LaunchedByCell entry={entry} />
      <CreatedAtCell entry={entry} />
      <TagsCell entry={entry} />
    </Box>
  );
};

export const RunsFeedTableHeader = () => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px 40px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '2px solid #d1d5db',
        fontWeight: 600,
        backgroundColor: '#f9fafb',
      }}
    >
      <Box>Launched by</Box>
      <Box>Created at</Box>
      <Box>Tags</Box>
    </Box>
  );
};
