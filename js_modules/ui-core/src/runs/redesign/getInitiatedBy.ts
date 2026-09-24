import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {buildTagMap, getRepoAddress} from './utils';
import {InstigationSelector} from '../../graphql/types';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {DagsterTag} from '../RunTag';

const DEFAULT_AUTOMATION_SENSOR_NAME = 'default_automation_condition_sensor';

export type Initiator =
  | {kind: 'reexecution'; parentRunId: string; isAutomatic: boolean}
  | {kind: 'schedule'; name: string; href: string | null}
  | {kind: 'sensor'; name: string; href: string | null}
  | {kind: 'declarative-automation'; label: string; href: string | null}
  | {kind: 'auto-observation'}
  | {kind: 'backfill'}
  | {kind: 'manual'};

export type TickIdentifier = {
  tickId: string;
  instigationSelector: InstigationSelector;
};

export type InitiatedBy = {
  initiator: Initiator;
  user: string | null;
  parentBackfillId: string | null;
  tick: TickIdentifier | null;
};

const getScheduleOrSensorPath = (repoAddress: RepoAddress | null, prefix: string, name: string) =>
  repoAddress !== null ? workspacePathFromAddress(repoAddress, `${prefix}/${name}`) : null;

const getInitiator = (
  entry: MappedRunsFeedEntry,
  tags: Map<string, string>,
  repoAddress: RepoAddress | null,
): Initiator => {
  // Re-execution wins; a parent backfill is still reported separately.
  if (entry.__typename === 'Run' && entry.parentRunId !== null) {
    return {
      kind: 'reexecution',
      parentRunId: entry.parentRunId,
      isAutomatic: entry.isAutomaticRetry,
    };
  }

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
        label: isDefaultSensor ? 'Declarative automation' : sensorName,
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
      label: 'Declarative automation',
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
const isLaunchedByUser = (initiator: Initiator) =>
  (initiator.kind === 'reexecution' && !initiator.isAutomatic) ||
  initiator.kind === 'backfill' ||
  initiator.kind === 'manual';

const getUser = (entry: MappedRunsFeedEntry, tags: Map<string, string>): string | null => {
  const taggedUser = tags.get(DagsterTag.User);
  if (taggedUser !== undefined) {
    return taggedUser;
  }

  return entry.__typename === 'PartitionBackfill' ? (entry.user ?? null) : null;
};

const getTick = (
  tags: Map<string, string>,
  repoAddress: RepoAddress | null,
): TickIdentifier | null => {
  if (repoAddress === null) {
    return null;
  }

  const tickId = tags.get(DagsterTag.TickId);
  const name = tags.get(DagsterTag.ScheduleName) ?? tags.get(DagsterTag.SensorName);
  if (tickId === undefined || name === undefined) {
    return null;
  }

  return {
    tickId,
    instigationSelector: {
      name,
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    },
  };
};

export const getInitiatedBy = (entry: MappedRunsFeedEntry): InitiatedBy => {
  const tags = buildTagMap(entry.tags);
  const repoAddress = getRepoAddress(entry);
  const initiator = getInitiator(entry, tags, repoAddress);

  return {
    initiator,
    user: isLaunchedByUser(initiator) ? getUser(entry, tags) : null,
    parentBackfillId: tags.get(DagsterTag.Backfill) ?? null,
    tick: getTick(tags, repoAddress),
  };
};
