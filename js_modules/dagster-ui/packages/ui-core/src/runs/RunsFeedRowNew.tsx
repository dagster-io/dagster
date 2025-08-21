import {
  Box,
  Button,
  Colors,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  Tag,
} from '@dagster-io/ui-components';
import {useState} from 'react';

import {DagsterTag} from './RunTag';
import {formatElapsedTimeWithoutMsec} from '../app/Util';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTableEntryFragment.types';
import {RunStatus} from '../graphql/types';

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

const StatusCell = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  const status = entry.runStatus;

  // Determine icon, color, and text based on status
  const getStatusConfig = (status: RunStatus) => {
    switch (status) {
      case RunStatus.SUCCESS:
        return {
          icon: 'run_success' as const,
          color: Colors.accentGreen(),
          text: 'Success',
          showDuration: true,
          showOnlyDuration: true,
        };
      case RunStatus.STARTED:
        return {
          color: Colors.accentBlue(),
          text: 'Started',
          showDuration: true,
          showOnlyDuration: true,
          useSpinner: true,
        };
      case RunStatus.FAILURE:
        return {
          icon: 'run_failed' as const,
          color: Colors.accentRed(),
          text: 'Failure',
          showDuration: true,
          showOnlyDuration: true,
        };
      case RunStatus.QUEUED:
        return {
          icon: 'hourglass_bottom' as const,
          color: Colors.textLight(),
          text: 'Queued',
          showDuration: false,
        };
      case RunStatus.STARTING:
        return {
          color: Colors.accentBlue(),
          text: 'Starting',
          showDuration: false,
          useSpinner: true,
        };
      case RunStatus.NOT_STARTED:
        return {
          icon: 'status' as const,
          color: Colors.textLight(),
          text: 'Not started',
          showDuration: false,
        };
      case RunStatus.CANCELING:
        return {
          color: Colors.accentBlue(),
          text: 'Cancelling',
          showDuration: false,
          useSpinner: true,
        };
      case RunStatus.CANCELED:
        return {
          icon: 'run_canceled' as const,
          color: Colors.textLight(),
          text: 'Cancelled',
          showDuration: false,
        };
      default:
        return {
          icon: 'status' as const,
          color: Colors.textLight(),
          text: 'Unknown',
          showDuration: false,
        };
    }
  };

  const config = getStatusConfig(status);

  // For SUCCESS, STARTED, FAILURE - show icon + duration in status text style
  if (config.showOnlyDuration && config.showDuration) {
    return (
      <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
        {config.useSpinner ? (
          <Spinner purpose="caption-text" />
        ) : config.icon ? (
          <Icon name={config.icon} data-kyle="asdfasdf" color={config.color} size={16} />
        ) : null}
        <Box
          style={{
            color: config.color,
            fontSize: '14px',
            fontWeight: 500,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {entry.startTime
            ? entry.endTime
              ? formatElapsedTimeWithoutMsec((entry.endTime - entry.startTime) * 1000)
              : formatElapsedTimeWithoutMsec((Date.now() / 1000 - entry.startTime) * 1000)
            : '–'}
        </Box>
      </Box>
    );
  }

  // For other statuses - show icon + text (no duration)
  return (
    <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
      {config.useSpinner ? (
        <Spinner purpose="caption-text" />
      ) : config.icon ? (
        <Icon name={config.icon} color={config.color} size={16} />
      ) : null}
      <Box style={{color: config.color, fontSize: '14px', fontWeight: 500}}>{config.text}</Box>
    </Box>
  );
};

const MoreActionsCell = ({entry: _entry}: {entry: RunsFeedTableEntryFragment}) => {
  return (
    <Button
      icon="more_horiz"
      style={{minWidth: 'auto', padding: '4px'}}
      onClick={(e) => {
        e.stopPropagation();
        // TODO: Implement more actions menu
      }}
    />
  );
};

export const RunsFeedRow = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px 120px 40px 40px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '1px solid #e1e5e9',
        alignItems: 'center',
      }}
    >
      <LaunchedByCell entry={entry} />
      <CreatedAtCell entry={entry} />
      <StatusCell entry={entry} />
      <TagsCell entry={entry} />
      <MoreActionsCell entry={entry} />
    </Box>
  );
};

export const RunsFeedTableHeader = () => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px 120px 40px 40px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '2px solid #d1d5db',
        fontWeight: 600,
        backgroundColor: '#f9fafb',
      }}
    >
      <Box>Launched by</Box>
      <Box>Created at</Box>
      <Box>Status</Box>
      <Box>Tags</Box>
      <Box></Box>
    </Box>
  );
};
