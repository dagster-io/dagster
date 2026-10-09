import {DagsterTag} from '../../RunTag';
import {
  assetBackfill,
  autoMaterializeRun,
  autoMaterializeTickRun,
  autoObserveRun,
  autoRetryInBackfillRun,
  backfillChildRun,
  backfillEntry,
  createdByAutoMaterializeRun,
  defaultAutomationSensorRun,
  defaultAutomationSensorRunNoRepo,
  manualRun,
  manualRunWithUser,
  namedAutomationSensorRun,
  reExecutionRun,
  runEntry,
  scheduleRun,
  scheduleRunWithTick,
  scheduleRunWithoutRepo,
  sensorRun,
  sensorRunWithTick,
  tag,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {Initiator, getLaunchDetails} from '../getLaunchDetails';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const SCHEDULE_PATH = '/locations/my_repo@my_location/schedules/hourly_schedule';
const SENSOR_PATH = '/locations/my_repo@my_location/sensors/files_sensor';

describe('getLaunchDetails', () => {
  it.each<[string, MappedRunsFeedEntry, Initiator]>([
    ['manual', manualRun, {kind: 'manual'}],
    ['schedule', scheduleRun, {kind: 'schedule', name: 'hourly_schedule', href: SCHEDULE_PATH}],
    [
      'schedule without repository origin',
      scheduleRunWithoutRepo,
      {kind: 'schedule', name: 'hourly_schedule', href: null},
    ],
    ['sensor', sensorRun, {kind: 'sensor', name: 'files_sensor', href: SENSOR_PATH}],
    [
      'default automation sensor',
      defaultAutomationSensorRun,
      {
        kind: 'declarative-automation',
        name: 'default_automation_condition_sensor',
        href: '/locations/my_repo@my_location/sensors/default_automation_condition_sensor',
      },
    ],
    [
      'named automation sensor',
      namedAutomationSensorRun,
      {
        kind: 'declarative-automation',
        name: 'my_automation_sensor',
        href: '/locations/my_repo@my_location/sensors/my_automation_sensor',
      },
    ],
    [
      'auto materialize tag',
      autoMaterializeRun,
      {kind: 'declarative-automation', name: null, href: null},
    ],
    [
      'legacy created_by tag',
      createdByAutoMaterializeRun,
      {kind: 'declarative-automation', name: null, href: null},
    ],
    ['auto observation', autoObserveRun, {kind: 'auto-observation'}],
    ['backfill', backfillChildRun, {kind: 'backfill'}],
  ])('classifies %s', (_name, entry, initiator) => {
    expect(getLaunchDetails(entry).initiator).toEqual(initiator);
  });

  it('classifies a re-execution by the launcher tags it inherits from its parent', () => {
    const entry = runEntry({
      parentRunId: 'parent-run-id',
      tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')],
    });
    expect(getLaunchDetails(entry).initiator).toEqual({
      kind: 'schedule',
      name: 'hourly_schedule',
      href: SCHEDULE_PATH,
    });
  });

  it('prefers declarative automation over a plain sensor for the same sensor tag', () => {
    const entry = runEntry({
      tags: [
        tag(DagsterTag.SensorName, 'files_sensor'),
        tag(DagsterTag.AutomationCondition, 'true'),
      ],
    });
    expect(getLaunchDetails(entry).initiator).toMatchObject({kind: 'declarative-automation'});
  });

  it('keeps the backfill but drops the inherited user for an automatic retry', () => {
    expect(getLaunchDetails(autoRetryInBackfillRun)).toEqual({
      initiator: {kind: 'backfill'},
      user: null,
      parentBackfillId: 'bkfl1234',
      tick: null,
    });
  });

  it('keeps the user for a manual re-execution', () => {
    expect(getLaunchDetails(reExecutionRun).user).toBe('pat@example.com');
  });

  it('keeps the user for a manual re-execution of a scheduled run', () => {
    const entry = runEntry({
      parentRunId: 'parent-run-id',
      tags: [
        tag(DagsterTag.ScheduleName, 'hourly_schedule'),
        tag(DagsterTag.User, 'pat@example.com'),
      ],
    });
    expect(getLaunchDetails(entry).user).toBe('pat@example.com');
  });

  it('reports the parent backfill for a backfill child run', () => {
    expect(getLaunchDetails(backfillChildRun)).toMatchObject({
      initiator: {kind: 'backfill'},
      parentBackfillId: 'bkfl1234',
    });
  });

  it.each([
    ['a user tag', manualRunWithUser, 'pat@example.com'],
    ['no user tag', manualRun, null],
  ])('reads the launching user from %s', (_name, entry, user) => {
    expect(getLaunchDetails(entry).user).toBe(user);
  });

  it.each([
    ['a schedule', tag(DagsterTag.ScheduleName, 'hourly_schedule')],
    ['a sensor', tag(DagsterTag.SensorName, 'files_sensor')],
    ['declarative automation', tag(DagsterTag.Automaterialize, 'true')],
    ['auto-observation', tag(DagsterTag.AutoObserve, 'true')],
  ])('drops the user tag when %s launched the run', (_name, launcherTag) => {
    const entry = runEntry({tags: [launcherTag, tag(DagsterTag.User, 'pat@example.com')]});
    expect(getLaunchDetails(entry).user).toBeNull();
  });

  it('falls back to the backfill user field when there is no user tag', () => {
    expect(getLaunchDetails(assetBackfill)).toMatchObject({
      initiator: {kind: 'manual'},
      user: 'pat@example.com',
    });
  });

  it('classifies a backfill entry from its own tags', () => {
    const entry = backfillEntry({tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')]});
    expect(getLaunchDetails(entry).initiator).toEqual({
      kind: 'schedule',
      name: 'hourly_schedule',
      href: null,
    });
  });

  it('builds a tick selector from the automation sensor and the repository origin', () => {
    expect(getLaunchDetails(defaultAutomationSensorRun).tick).toEqual({
      tickId: 'tick-id',
      instigationSelector: {
        name: 'default_automation_condition_sensor',
        repositoryName: 'my_repo',
        repositoryLocationName: 'my_location',
      },
    });
  });

  it.each([
    ['the run is from a schedule', scheduleRunWithTick],
    ['the run is from a standard sensor', sensorRunWithTick],
    ['the repository origin is missing', defaultAutomationSensorRunNoRepo],
    ['an automation run has no sensor name', autoMaterializeTickRun],
    ['there is no tick tag', namedAutomationSensorRun],
  ])('omits the tick when %s', (_name, entry) => {
    expect(getLaunchDetails(entry).tick).toBeNull();
  });
});
