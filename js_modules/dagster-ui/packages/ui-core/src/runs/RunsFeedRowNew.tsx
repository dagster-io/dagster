import {Box, Tag} from '@dagster-io/ui-components';

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

export const RunsFeedRow = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '1px solid #e1e5e9',
        alignItems: 'center',
      }}
    >
      <LaunchedByCell entry={entry} />
      <CreatedAtCell entry={entry} />
    </Box>
  );
};

export const RunsFeedTableHeader = () => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '2px solid #d1d5db',
        fontWeight: 600,
        backgroundColor: '#f9fafb',
      }}
    >
      <Box>Launched by</Box>
      <Box>Created at</Box>
    </Box>
  );
};
