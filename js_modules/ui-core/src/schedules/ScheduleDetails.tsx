import {Box, Code, Heading, PageHeader, Tag, Text} from '@dagster-io/ui-components';
import {ScheduleAlertDetails} from '@shared/schedules/ScheduleAlertDetails';
import {Link} from 'react-router-dom';

import {SchedulePartitionStatus} from './SchedulePartitionStatus';
import {ScheduleResetButton} from './ScheduleResetButton';
import {ScheduleSwitch} from './ScheduleSwitch';
import {TimestampDisplay} from './TimestampDisplay';
import styles from './css/ScheduleDetails.module.css';
import {humanCronString} from './humanCronString';
import {ScheduleFragment} from './types/ScheduleUtils.types';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {useIsMobile} from '../app/layout/IsMobileContext';
import {AutomationTargetList} from '../automation/AutomationTargetList';
import sectionStyles from '../automation/css/AutomationDetailsSections.module.css';
import {AutomationAssetSelectionFragment} from '../automation/types/AutomationAssetSelectionFragment.types';
import {InstigationStatus} from '../graphql/types';
import {RepositoryLink} from '../nav/RepositoryLink';
import {DefinitionOwners} from '../owners/DefinitionOwners';
import {EvaluateTickButtonSchedule} from '../ticks/EvaluateTickButtonSchedule';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {AttributeAndValue, NoValue} from '../ui/AttributeAndValue';
import {LargeCollapsibleSection} from '../ui/LargeCollapsibleSection';
import {RepoAddress} from '../workspace/types';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

export const ScheduleDetails = (props: {
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
  refreshState: QueryRefreshState;
  assetSelection: AutomationAssetSelectionFragment | null;
}) => {
  const {repoAddress, schedule, refreshState, assetSelection} = props;
  const {cronSchedule, executionTimezone, futureTicks, name, partitionSet, pipelineName} = schedule;
  const {scheduleState} = schedule;
  const {status, ticks} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;
  const running = status === InstigationStatus.RUNNING;
  const isMobile = useIsMobile();

  return (
    <>
      <PageHeader
        title={
          <Heading
            size={16}
            weight={600}
            className={styles.title}
            style={{display: 'flex', flexDirection: 'row', gap: 4}}
          >
            <Link to="/automation">Automation</Link>
            <span>/</span>
            {name}
          </Heading>
        }
        tags={
          <Tag icon="schedule">
            Schedule in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
        right={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <QueryRefreshCountdown refreshState={refreshState} />
            <EvaluateTickButtonSchedule
              name={schedule.name}
              repoAddress={repoAddress}
              jobName={pipelineName}
            />
          </Box>
        }
      />
      <div className={sectionStyles.sections}>
        <LargeCollapsibleSection header="Status" icon="status" storageKey="automation-status">
          <div className={sectionStyles.attributeGrid}>
            <AttributeAndValue label="Latest tick">
              {latestTick ? (
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center', wrap: 'wrap'}}>
                  <TimestampDisplay
                    timestamp={latestTick.timestamp}
                    timezone={executionTimezone}
                    timeFormat={TIME_FORMAT}
                  />
                  <TickStatusTag tick={latestTick} tickResultType="runs" />
                </Box>
              ) : (
                'Schedule has never run'
              )}
            </AttributeAndValue>
            <AttributeAndValue label="Next tick">
              {futureTicks.results[0] && running ? (
                <TimestampDisplay
                  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                  timestamp={futureTicks.results[0].timestamp!}
                  timezone={executionTimezone}
                  timeFormat={TIME_FORMAT}
                />
              ) : (
                <NoValue />
              )}
            </AttributeAndValue>
            <AttributeAndValue label="Running">
              {/* Sized to the reset button, so the row is the same height when it's absent. */}
              <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}} style={{minHeight: 32}}>
                <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
                {schedule.canReset && (
                  <ScheduleResetButton repoAddress={repoAddress} schedule={schedule} />
                )}
              </Box>
            </AttributeAndValue>
          </div>
        </LargeCollapsibleSection>
        <LargeCollapsibleSection
          header="Definition"
          icon="info"
          storageKey="automation-definition"
          collapsedByDefault={isMobile}
        >
          <Box flex={{direction: 'column', gap: 16}}>
            <div className={sectionStyles.attributeGrid}>
              <AttributeAndValue label="Schedule">
                {cronSchedule ? (
                  <Box flex={{direction: 'column', gap: 4}}>
                    <Box
                      className={styles.cronRow}
                      flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}
                    >
                      <span>
                        {humanCronString(cronSchedule, {
                          longTimezoneName: executionTimezone || 'UTC',
                        })}
                      </span>
                      <Code>({cronSchedule})</Code>
                    </Box>
                    {executionTimezone ? (
                      <Text size={12} color="textLighter">
                        Timezone: {executionTimezone}
                      </Text>
                    ) : null}
                  </Box>
                ) : (
                  <NoValue />
                )}
              </AttributeAndValue>
              {schedule.pipelineName || assetSelection ? (
                <AttributeAndValue label="Target">
                  <div className={sectionStyles.targetCell}>
                    <AutomationTargetList
                      targets={
                        schedule.pipelineName ? [{pipelineName: schedule.pipelineName}] : null
                      }
                      repoAddress={repoAddress}
                      assetSelection={assetSelection || null}
                      automationType="schedule"
                    />
                  </div>
                </AttributeAndValue>
              ) : null}
              <AttributeAndValue label="Partition set">
                {partitionSet ? (
                  <SchedulePartitionStatus schedule={schedule} repoAddress={repoAddress} />
                ) : (
                  <NoValue />
                )}
              </AttributeAndValue>
              {schedule.owners.length > 0 && (
                <AttributeAndValue label="Owners">
                  <DefinitionOwners owners={schedule.owners} />
                </AttributeAndValue>
              )}
            </div>
            <AttributeAndValue label="Description">{schedule.description}</AttributeAndValue>
          </Box>
        </LargeCollapsibleSection>
        <ScheduleAlertDetails repoAddress={repoAddress} scheduleName={name} />
      </div>
    </>
  );
};
