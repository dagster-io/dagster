import {DagsterTag} from '../../RunTag';
import {
  assetBackfill,
  autoMaterializeRun,
  autoObserveRun,
  autoRetryInBackfillRun,
  backfillChildRun,
  backfillEntry,
  createdByAutoMaterializeRun,
  defaultAutomationSensorRun,
  legacyAutomationConditionTickRun,
  manualRun,
  manualRunWithUser,
  namedAutomationSensorRun,
  reExecutionRun,
  runEntry,
  scheduleRun,
  scheduleRunWithTick,
  scheduleRunWithTickNoRepo,
  scheduleRunWithoutRepo,
  sensorRun,
  tag,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {Initiator, getInitiatedBy} from '../getInitiatedBy';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const SCHEDULE_PATH = '/locations/my_repo@my_location/schedules/hourly_schedule';
const SENSOR_PATH = '/locations/my_repo@my_location/sensors/files_sensor';

describe('getInitiatedBy', () => {
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
        label: 'Declarative automation',
        href: '/locations/my_repo@my_location/sensors/default_automation_condition_sensor',
      },
    ],
    [
      'named automation sensor',
      namedAutomationSensorRun,
      {
        kind: 'declarative-automation',
        label: 'my_automation_sensor',
        href: '/locations/my_repo@my_location/sensors/my_automation_sensor',
      },
    ],
    [
      'auto materialize tag',
      autoMaterializeRun,
      {kind: 'declarative-automation', label: 'Declarative automation', href: null},
    ],
    [
      'legacy created_by tag',
      createdByAutoMaterializeRun,
      {kind: 'declarative-automation', label: 'Declarative automation', href: null},
    ],
    ['auto observation', autoObserveRun, {kind: 'auto-observation'}],
    ['backfill', backfillChildRun, {kind: 'backfill'}],
    [
      're-execution',
      reExecutionRun,
      {
        kind: 'reexecution',
        parentRunId: 'pppppppp-1111-2222-3333-444455556666',
        isAutomatic: false,
      },
    ],
  ])('classifies %s', (_name, entry, initiator) => {
    expect(getInitiatedBy(entry).initiator).toEqual(initiator);
  });

  it('prefers a re-execution over the schedule that launched the original run', () => {
    const entry = runEntry({
      parentRunId: 'parent-run-id',
      tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')],
    });
    expect(getInitiatedBy(entry).initiator).toEqual({
      kind: 'reexecution',
      parentRunId: 'parent-run-id',
      isAutomatic: false,
    });
  });

  it('prefers declarative automation over a plain sensor for the same sensor tag', () => {
    const entry = runEntry({
      tags: [
        tag(DagsterTag.SensorName, 'files_sensor'),
        tag(DagsterTag.AutomationCondition, 'true'),
      ],
    });
    expect(getInitiatedBy(entry).initiator).toMatchObject({kind: 'declarative-automation'});
  });

  it('keeps the backfill but drops the inherited user for an automatic retry', () => {
    expect(getInitiatedBy(autoRetryInBackfillRun)).toEqual({
      initiator: {
        kind: 'reexecution',
        parentRunId: 'pppppppp-1111-2222-3333-444455556666',
        isAutomatic: true,
      },
      user: null,
      parentBackfillId: 'bkfl1234',
      tick: null,
    });
  });

  it('keeps the user for a manual re-execution', () => {
    expect(getInitiatedBy(reExecutionRun).user).toBe('pat@example.com');
  });

  it('reports the parent backfill for a backfill child run', () => {
    expect(getInitiatedBy(backfillChildRun)).toMatchObject({
      initiator: {kind: 'backfill'},
      parentBackfillId: 'bkfl1234',
    });
  });

  it.each([
    ['a user tag', manualRunWithUser, 'pat@example.com'],
    ['no user tag', manualRun, null],
  ])('reads the launching user from %s', (_name, entry, user) => {
    expect(getInitiatedBy(entry).user).toBe(user);
  });

  it.each([
    ['a schedule', tag(DagsterTag.ScheduleName, 'hourly_schedule')],
    ['a sensor', tag(DagsterTag.SensorName, 'files_sensor')],
    ['declarative automation', tag(DagsterTag.Automaterialize, 'true')],
    ['auto-observation', tag(DagsterTag.AutoObserve, 'true')],
  ])('drops the user tag when %s launched the run', (_name, launcherTag) => {
    const entry = runEntry({tags: [launcherTag, tag(DagsterTag.User, 'pat@example.com')]});
    expect(getInitiatedBy(entry).user).toBeNull();
  });

  it('falls back to the backfill user field when there is no user tag', () => {
    expect(getInitiatedBy(assetBackfill)).toMatchObject({
      initiator: {kind: 'manual'},
      user: 'pat@example.com',
    });
  });

  it('classifies a backfill entry from its own tags', () => {
    const entry = backfillEntry({tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')]});
    expect(getInitiatedBy(entry).initiator).toEqual({
      kind: 'schedule',
      name: 'hourly_schedule',
      href: null,
    });
  });

  it('builds a tick selector from the instigator name and the repository origin', () => {
    expect(getInitiatedBy(scheduleRunWithTick).tick).toEqual({
      tickId: 'tick-id',
      instigationSelector: {
        name: 'hourly_schedule',
        repositoryName: 'my_repo',
        repositoryLocationName: 'my_location',
      },
    });
  });

  it.each([
    ['the repository origin is missing', scheduleRunWithTickNoRepo],
    ['no instigator name accompanies the tick', legacyAutomationConditionTickRun],
    ['there is no tick tag', scheduleRun],
  ])('omits the tick when %s', (_name, entry) => {
    expect(getInitiatedBy(entry).tick).toBeNull();
  });
});
