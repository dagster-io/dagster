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
import {useState, useEffect} from 'react';

import {DagsterTag} from './RunTag';
import {RunStats} from './RunStats';
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

  const renderLaunchInfo = (iconName: string, text: string) => (
    <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
      <Icon name={iconName} size={16} />
      <span>{text}</span>
    </Box>
  );

  switch (launchType.type) {
    case 'manual':
      return renderLaunchInfo('account_circle', launchType.user);
    case 'schedule':
      return renderLaunchInfo('schedule', launchType.name);
    case 'sensor':
      return renderLaunchInfo('sensors', launchType.name);
    case 'automation':
      return renderLaunchInfo('automation_condition', 'Declarative automation');
    case 'backfill-launched':
      return renderLaunchInfo('settings_backup_restore', `Backfill (${launchType.backfillId})`);
    default:
      return renderLaunchInfo('account_circle', 'Manual');
  }
};

const getStatusName = (status: RunStatus): string => {
  switch (status) {
    case RunStatus.SUCCESS:
      return 'Success';
    case RunStatus.STARTED:
      return 'Started';
    case RunStatus.FAILURE:
      return 'Failure';
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.STARTING:
      return 'Starting';
    case RunStatus.NOT_STARTED:
      return 'Not started';
    case RunStatus.CANCELING:
      return 'Cancelling';
    case RunStatus.CANCELED:
      return 'Cancelled';
    default:
      return 'Unknown';
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
                    icon={<Icon name="more_horiz" />}
                    intent="none"
                    style={{
                      marginLeft: '8px',
                      minWidth: 'auto',
                      width: '32px',
                      height: '32px',
                      padding: '4px',
                      border: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
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
      <Button 
        icon={<Icon name="data_object" />} 
        intent="none"
        style={{
          minWidth: 'auto', 
          width: '32px', 
          height: '32px', 
          padding: '4px', 
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }} 
      />
    </Popover>
  );
};

const StatusCell = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(Date.now());
  const status = entry.runStatus;
  
  // Update current time every second for started runs
  useEffect(() => {
    if (status === RunStatus.STARTED) {
      const interval = setInterval(() => {
        setCurrentTime(Date.now());
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [status]);

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
  const runIdShort = entry.id.slice(0, 8);
  
  // Mock data for steps (always 3 expected, random 0-3 completed)
  const stepsCompleted = Math.floor(Math.random() * 4); // 0, 1, 2, or 3
  const stepsExpected = 3;
  
  // Assets materialized based on assetSelection length
  const assetsExpected = entry.assetSelection?.length || 0;
  const assetsCompleted = assetsExpected > 0 ? Math.floor(Math.random() * (assetsExpected + 1)) : 0;
  
  // Asset checks based on assetCheckSelection length
  const checksExpected = entry.assetCheckSelection?.length || 0;
  const checksCompleted = checksExpected > 0 ? Math.floor(Math.random() * (checksExpected + 1)) : 0;

  const getTagVariant = (completed: number, expected: number) => {
    if (expected === 0) return 'default';
    if (completed >= expected) return 'green';
    return 'red';
  };

  const renderStatusContent = () => {
    if (config.showOnlyDuration && config.showDuration) {
      return (
        <Box style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%'}}>
          <Box style={{width: '16px', display: 'flex', alignItems: 'center', justifyContent: 'flex-start'}}>
            {config.useSpinner ? (
              <Box style={{margin: 'auto'}} className="spinner-wrapper">
                <style>{`.spinner-wrapper svg path { stroke: ${config.color} !important; }`}</style>
                <Spinner purpose="body-text" />
              </Box>
            ) : config.icon ? (
              <Icon name={config.icon} size={16} style={{margin: 'auto', backgroundColor: config.color}} />
            ) : null}
          </Box>
          <Box
            style={{
              color: config.color,
              fontSize: '14px',
              fontWeight: 400,
              lineHeight: '20px',
              fontVariantNumeric: 'tabular-nums',
              width: '6em',
              textAlign: 'right',
            }}
          >
            {entry.startTime
              ? entry.endTime
                ? formatElapsedTimeWithoutMsec((entry.endTime - entry.startTime) * 1000)
                : formatElapsedTimeWithoutMsec((currentTime / 1000 - entry.startTime) * 1000)
              : '–'}
          </Box>
        </Box>
      );
    }

    return (
      <Box style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%'}}>
        <Box style={{width: '16px', display: 'flex', alignItems: 'center', justifyContent: 'flex-start'}}>
          {config.useSpinner ? (
            <Box style={{margin: 'auto'}} className="spinner-wrapper">
              <style>{`.spinner-wrapper svg path { stroke: ${config.color} !important; }`}</style>
              <Spinner purpose="body-text" />
            </Box>
          ) : config.icon ? (
            <Icon name={config.icon} size={16} style={{margin: 'auto', backgroundColor: config.color}} />
          ) : null}
        </Box>
        <Box 
          style={{
            color: config.color, 
            fontSize: '14px', 
            fontWeight: 400,
            lineHeight: '20px',
            width: '6em',
            textAlign: 'right',
          }}
        >
          {config.text}
        </Box>
      </Box>
    );
  };

  return (
    <Box style={{display: 'flex', justifyContent: 'flex-end'}}>
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
              <Icon name="status" size={16} />
              <span style={{fontWeight: 500}}>{getStatusName(status)}</span>
            </Box>
            <Box style={{color: '#64748b', fontSize: '12px'}}>#{runIdShort}</Box>
          </Box>

          {/* Job name section */}
          {entry.jobName && (
            <Box
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '12px',
              }}
            >
              <Box style={{fontWeight: 500, color: '#374151'}}>Job name:</Box>
              <Tag intent="none">{entry.jobName}</Tag>
            </Box>
          )}

          {/* Steps executed */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px',
            }}
          >
            <Box style={{fontWeight: 500, color: '#374151'}}>Steps executed:</Box>
            <Tag intent={getTagVariant(stepsCompleted, stepsExpected)}>
              {stepsCompleted}/{stepsExpected}
            </Tag>
          </Box>

          {/* Assets materialized */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px',
            }}
          >
            <Box style={{fontWeight: 500, color: '#374151'}}>Assets materialized:</Box>
            <Tag intent={getTagVariant(assetsCompleted, assetsExpected)}>
              {assetsCompleted}/{assetsExpected}
            </Tag>
          </Box>

          {/* Asset checks evaluated */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px',
            }}
          >
            <Box style={{fontWeight: 500, color: '#374151'}}>Asset checks evaluated:</Box>
            <Tag intent={getTagVariant(checksCompleted, checksExpected)}>
              {checksCompleted}/{checksExpected}
            </Tag>
          </Box>

          {/* View selection button */}
          <Button style={{width: '100%'}} intent="none">
            View selection
          </Button>
        </Box>
      }
    >
      <Button
        onClick={() => setIsOpen(true)}
        intent="none"
        style={{
          minWidth: 'auto',
          width: 'auto',
          height: '32px',
          padding: '0 12px',
          border: 'none',
          background: 'transparent',
          borderRadius: '6px',
        }}
      >
        {renderStatusContent()}
      </Button>
    </Popover>
    </Box>
  );
};

const MoreActionsCell = ({entry: _entry}: {entry: RunsFeedTableEntryFragment}) => {
  return (
    <Button
      icon={<Icon name="more_horiz" />}
      intent="none"
      style={{
        minWidth: 'auto', 
        width: '32px', 
        height: '32px', 
        padding: '4px', 
        border: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
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
        gridTemplateColumns: '1fr 120px 40px 150px 40px',
        gap: '12px',
        padding: '8px 12px',
        borderBottom: '1px solid #e1e5e9',
        alignItems: 'center',
      }}
    >
      <LaunchedByCell entry={entry} />
      <CreatedAtCell entry={entry} />
      <TagsCell entry={entry} />
      <StatusCell entry={entry} />
      <MoreActionsCell entry={entry} />
    </Box>
  );
};

export const RunsFeedTableHeader = () => {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 120px 40px 150px 40px',
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
      <Box style={{textAlign: 'right', paddingRight: '12px'}}>Status</Box>
      <Box></Box>
    </Box>
  );
};
