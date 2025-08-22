import {
  Box,
  Button,
  Checkbox,
  Colors,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import {useState, useEffect, useMemo} from 'react';

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
    <Box style={{display: 'flex', alignItems: 'center', gap: '6px', width: '248px', paddingRight: '12px', borderRight: '1px solid #d1d5db'}}>
      <Icon name={iconName} size={16} color={Colors.accentBlue()} />
      <span style={{overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}} title={text}>{text}</span>
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
  return <Box style={{fontSize: '14px', width: '88px', paddingRight: '12px', borderRight: '1px solid #d1d5db'}}>{createdAtText}</Box>;
};

const TagsCell = ({entry}: {entry: RunsFeedTableEntryFragment}) => {
  const [isOpen, setIsOpen] = useState(false);
  const tags = (entry.tags || []).slice().sort((a, b) => {
    const keyA = a.key.startsWith('dagster/') ? a.key.replace('dagster/', '') : a.key;
    const keyB = b.key.startsWith('dagster/') ? b.key.replace('dagster/', '') : b.key;
    return keyA.localeCompare(keyB);
  });

  const runIdShort = entry.id.slice(0, 8);

  return (
    <Box style={{width: '76px'}}>
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
              <Icon name="data_object" size={16} style={{backgroundColor: Colors.accentBlue()}} />
              <span style={{fontSize: '18px', fontWeight: 600}}>Tags</span>
            </Box>
            <Box style={{fontFamily: 'Geist Mono', fontSize: '14px', lineHeight: '20px', color: '#64748b'}}>#{runIdShort}</Box>
          </Box>

          {/* Tags List */}
          <Box style={{display: 'flex', gap: '24px', marginBottom: '12px'}}>
            {/* Keys Column */}
            <Box style={{display: 'flex', flexDirection: 'column', maxWidth: '200px'}}>
              {tags.map((tag, index) => {
                const isDagsterTag = tag.key.startsWith('dagster/');
                const displayKey = isDagsterTag ? tag.key.replace('dagster/', '') : tag.key;
                
                return (
                  <Box
                    key={`key-${index}`}
                    style={{
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <Box
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '0 6px',
                        fontSize: '14px',
                        fontWeight: 600,
                        color: Colors.textDefault(),
                        cursor: 'pointer',
                        borderRadius: '8px',
                        gap: '4px',
                        maxWidth: '100%',
                        overflow: 'hidden',
                        height: '32px',
                      }}
                      className="tag-item"
                    >
                      <Box style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}>
                        {displayKey}:
                      </Box>
                      <Box
                        style={{
                          width: '16px',
                          height: '16px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          opacity: 0,
                          transition: 'opacity 0.15s ease'
                        }}
                        className="copy-icon"
                      >
                        <Icon name="content_copy" size={16} color={Colors.accentGray()} />
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </Box>
            
            {/* Values Column */}
            <Box style={{display: 'flex', flexDirection: 'column', flex: 1, maxWidth: '200px'}}>
              {tags.map((tag, index) => {
                return (
                  <Box
                    key={`value-${index}`}
                    style={{
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <Box
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '0 6px',
                        fontSize: '14px',
                        fontWeight: 400,
                        color: Colors.textDefault(),
                        cursor: 'pointer',
                        borderRadius: '8px',
                        gap: '4px',
                        maxWidth: '100%',
                        overflow: 'hidden',
                        height: '32px',
                      }}
                      className="tag-item"
                    >
                      <Box style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}>
                        {tag.value}
                      </Box>
                      <Box
                        style={{
                          width: '16px',
                          height: '16px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          opacity: 0,
                          transition: 'opacity 0.15s ease'
                        }}
                        className="copy-icon"
                      >
                        <Icon name="content_copy" size={16} color={Colors.accentGray()} />
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </Box>
            
            {/* Actions Column */}
            <Box style={{display: 'flex', flexDirection: 'column'}}>
              {tags.map((tag, index) => {
                return (
                  <Box
                    key={`actions-${index}`}
                    style={{
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Tooltip content="Copy key/value pair">
                      <Button
                        icon={<Icon name="content_copy" />}
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
                          // TODO: Implement copy functionality
                        }}
                      />
                    </Tooltip>
                    <Tooltip content="Add tag to view">
                      <Button
                        icon={<Icon name="add" />}
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
                          // TODO: Implement add to filters functionality
                        }}
                      />
                    </Tooltip>
                  </Box>
                );
              })}
            </Box>
          </Box>

          {/* Copy All Button */}
          <Button onClick={() => {}} style={{border: '1px solid #d1d5db'}} intent="none">
            Copy all
          </Button>
          
          <style>{`
            .tag-item:hover {
              background-color: ${Colors.backgroundGray()} !important;
            }
            
            .tag-item:hover .copy-icon {
              opacity: 1 !important;
            }
          `}</style>
        </Box>
      }
    >
      <Button 
        icon={<Icon name="data_object" style={{backgroundColor: Colors.accentBlue()}} />} 
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
    </Box>
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
  
  // Memoize mock data so it doesn't change on every render (especially for Started runs)
  const mockData = useMemo(() => {
    // Debug: Log the actual data
    console.log('assetSelection:', entry.assetSelection);
    console.log('assetCheckSelection:', entry.assetCheckSelection);
    
    // Mock data for steps (always 3 expected, random 0-3 completed)
    const stepsCompleted = Math.floor(Math.random() * 4); // 0, 1, 2, or 3
    const stepsExpected = 3;
    
    // Assets materialized - use real data from GraphQL with fallback for mocking
    const assetsExpected = entry.assetSelection?.length || Math.floor(Math.random() * 6) + 1; // 1-6 fallback
    const assetsCompleted = Math.floor(Math.random() * (assetsExpected + 1));
    
    // Asset checks - use real data from GraphQL with fallback for mocking
    const checksExpected = entry.assetCheckSelection?.length || Math.floor(Math.random() * 4) + 1; // 1-4 fallback  
    const checksCompleted = Math.floor(Math.random() * (checksExpected + 1));
    
    return {
      stepsCompleted,
      stepsExpected,
      assetsExpected,
      assetsCompleted,
      checksExpected,
      checksCompleted,
    };
  }, [entry.id, entry.assetSelection?.length, entry.assetCheckSelection?.length]); // Only recalculate if entry ID or selection lengths change

  const getTagVariant = (completed: number, expected: number) => {
    if (expected === 0) return 'none';
    if (completed >= expected) return 'success';
    return 'danger';
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
              {config.useSpinner ? (
                <Box className="spinner-wrapper">
                  <style>{`.spinner-wrapper svg path { stroke: ${config.color} !important; }`}</style>
                  <Spinner purpose="body-text" />
                </Box>
              ) : config.icon ? (
                <Icon name={config.icon} size={16} style={{backgroundColor: config.color}} />
              ) : null}
              <span style={{fontSize: '18px', fontWeight: 600}}>{getStatusName(status)}</span>
            </Box>
            <Box style={{fontFamily: 'Geist Mono', fontSize: '14px', lineHeight: '20px', color: '#64748b'}}>#{runIdShort}</Box>
          </Box>

          {/* Job name section */}
          {entry.jobName && (
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
                <Icon name="job" size={16} />
                <span style={{fontSize: '14px', fontWeight: 400, color: Colors.textDefault()}}>Job name:</span>
              </Box>
              <Tag intent="none">{entry.jobName}</Tag>
            </Box>
          )}

          {/* Steps executed */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              height: '32px',
            }}
          >
            <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <Icon name="op" size={16} />
              <span style={{fontSize: '14px', fontWeight: 400, color: Colors.textDefault()}}>Steps executed:</span>
            </Box>
            <Tag intent={getTagVariant(mockData.stepsCompleted, mockData.stepsExpected)}>
              {mockData.stepsCompleted}/{mockData.stepsExpected}
            </Tag>
          </Box>

          {/* Assets materialized */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              height: '32px',
            }}
          >
            <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <Icon name="asset" size={16} />
              <span style={{fontSize: '14px', fontWeight: 400, color: Colors.textDefault()}}>Assets materialized:</span>
            </Box>
            <Tag intent={getTagVariant(mockData.assetsCompleted, mockData.assetsExpected)}>
              {mockData.assetsCompleted}/{mockData.assetsExpected}
            </Tag>
          </Box>

          {/* Asset checks evaluated */}
          <Box
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              height: '32px',
            }}
          >
            <Box style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <Icon name="asset_check" size={16} />
              <span style={{fontSize: '14px', fontWeight: 400, color: Colors.textDefault()}}>Asset checks evaluated:</span>
            </Box>
            <Tag intent={getTagVariant(mockData.checksCompleted, mockData.checksExpected)}>
              {mockData.checksCompleted}/{mockData.checksExpected}
            </Tag>
          </Box>

          {/* View selection button */}
          <Button style={{border: '1px solid #d1d5db'}} intent="none">
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
        display: 'flex',
        justifyContent: 'space-between',
        padding: '8px 12px',
        borderBottom: '1px solid #e1e5e9',
        alignItems: 'center',
        backgroundColor: 'var(--color-background-default)',
        height: '56px',
        color: Colors.textLight(),
      }}
    >
      {/* Left group: Checkbox, Launched by, Created at, Tags */}
      <Box style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
        <Checkbox checked={false} size="small" />
        <LaunchedByCell entry={entry} />
        <CreatedAtCell entry={entry} />
        <TagsCell entry={entry} />
      </Box>
      
      {/* Right group: Status, More actions */}
      <Box style={{display: 'flex', alignItems: 'center', gap: '24px'}}>
        <StatusCell entry={entry} />
        <MoreActionsCell entry={entry} />
      </Box>
    </Box>
  );
};

export const RunsFeedTableHeader = () => {
  return (
    <Box
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        paddingTop: '12px',
        paddingBottom: '8px',
        paddingLeft: '12px',
        paddingRight: '12px',
        borderBottom: '1px solid #e1e5e9',
        fontSize: '14px',
        fontWeight: 400,
        color: Colors.textLighter(),
        backgroundColor: 'var(--color-background-default)',
        alignItems: 'center',
      }}
    >
      {/* Left group headers */}
      <Box style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
        <Checkbox checked={false} size="small" /> {/* Select All checkbox */}
        <Box style={{width: '248px', paddingRight: '12px', textAlign: 'left'}}>Launched by</Box>
        <Box style={{width: '88px', paddingRight: '12px', textAlign: 'left'}}>Created at</Box>
        <Box style={{width: '76px', textAlign: 'left'}}>Tags</Box>
      </Box>
      
      {/* Right group headers */}
      <Box style={{display: 'flex', alignItems: 'center', gap: '24px'}}>
        <Box style={{textAlign: 'right', paddingRight: '12px'}}>Status</Box>
        <Button
          icon={<Icon name="checklist" />}
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
          onClick={() => {
            // TODO: Implement bulk actions functionality
          }}
        />
      </Box>
    </Box>
  );
};
