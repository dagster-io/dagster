import {buildTagMap} from './buildTagMap';
import {getRepoAddress} from './getRepoAddress';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {InstigationSelector} from '../../graphql/types';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {DagsterTag} from '../RunTag';

const DEFAULT_AUTOMATION_SENSOR_NAME = 'default_automation_condition_sensor';

export type Initiator =
  | {kind: 'schedule'; name: string; href: string | null}
  | {kind: 'sensor'; name: string; href: string | null}
  | {kind: 'declarative-automation'; name: string | null; href: string | null}
  | {kind: 'auto-observation'}
  | {kind: 'backfill'}
  | {kind: 'manual'};

export type TickIdentifier = {
  tickId: string;
  instigationSelector: InstigationSelector;
};

export type LaunchDetails = {
  initiator: Initiator;
  user: string | null;
  parentBackfillId: string | null;
  tick: TickIdentifier | null;
};

const getScheduleOrSensorPath = (repoAddress: RepoAddress | null, prefix: string, name: string) =>
  repoAddress !== null ? workspacePathFromAddress(repoAddress, `${prefix}/${name}`) : null;

const getInitiator = (tags: Map<string, string>, repoAddress: RepoAddress | null): Initiator => {
  const scheduleName = tags.get(DagsterTag.ScheduleName);
  if (scheduleName !== undefined) {
    return {
      kind: 'schedule',
      name: scheduleName,
      href: getScheduleOrSensorPath(repoAddress, '/schedules', scheduleName),
    };
  }

  const sensorName = tags.get(DagsterTag.SensorName);
  if (sensorName !== undefined) {
    const href = getScheduleOrSensorPath(repoAddress, '/sensors', sensorName);
    const isDefaultSensor = sensorName === DEFAULT_AUTOMATION_SENSOR_NAME;

    if (isDefaultSensor || tags.has(DagsterTag.AutomationCondition)) {
      return {
        kind: 'declarative-automation',
        name: sensorName,
        href,
      };
    }

    return {
      kind: 'sensor',
      name: sensorName,
      href,
    };
  }

  if (
    tags.has(DagsterTag.Automaterialize) ||
    tags.get(DagsterTag.CreatedBy) === 'auto_materialize'
  ) {
    return {
      kind: 'declarative-automation',
      name: null,
      href: null,
    };
  }

  if (tags.has(DagsterTag.AutoObserve)) {
    return {kind: 'auto-observation'};
  }

  if (tags.has(DagsterTag.Backfill)) {
    return {kind: 'backfill'};
  }

  return {kind: 'manual'};
};

// Automation is its own actor, and an automatic retry only inherits its parent's user tag.
const isLaunchedByUser = (entry: MappedRunsFeedEntry, initiator: Initiator) => {
  if (entry.__typename === 'Run' && entry.parentRunId !== null) {
    return !entry.isAutomaticRetry;
  }

  return initiator.kind === 'backfill' || initiator.kind === 'manual';
};

const getUser = (entry: MappedRunsFeedEntry, tags: Map<string, string>): string | null => {
  const taggedUser = tags.get(DagsterTag.User);
  if (taggedUser !== undefined) {
    return taggedUser;
  }

  return entry.__typename === 'PartitionBackfill' ? (entry.user ?? null) : null;
};

// Only declarative automation ticks explain why a run happened; other ticks repeat the row.
const getTick = (
  tags: Map<string, string>,
  repoAddress: RepoAddress | null,
  initiator: Initiator,
): TickIdentifier | null => {
  if (repoAddress === null || initiator.kind !== 'declarative-automation') {
    return null;
  }

  const tickId = tags.get(DagsterTag.TickId);
  if (tickId === undefined || initiator.name === null) {
    return null;
  }

  return {
    tickId,
    instigationSelector: {
      name: initiator.name,
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    },
  };
};

export const getLaunchDetails = (entry: MappedRunsFeedEntry): LaunchDetails => {
  const tags = buildTagMap(entry.tags);
  const repoAddress = getRepoAddress(entry);
  const initiator = getInitiator(tags, repoAddress);

  return {
    initiator,
    user: isLaunchedByUser(entry, initiator) ? getUser(entry, tags) : null,
    parentBackfillId: tags.get(DagsterTag.Backfill) ?? null,
    tick: getTick(tags, repoAddress, initiator),
  };
};
