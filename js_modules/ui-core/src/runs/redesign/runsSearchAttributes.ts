import {DagsterTag} from '../RunTag';

export const RUNS_SEARCH_ATTRIBUTES = [
  'id',
  'status',
  'job',
  'code_location',
  'sensor',
  'schedule',
  'user',
  'backfill',
  'partition',
  'tag',
  'snapshot_id',
  'created_after',
  'created_before',
] as const;

export type RunsSearchAttribute = (typeof RUNS_SEARCH_ATTRIBUTES)[number];

const TAG_BACKED_ATTRIBUTES = [
  'code_location',
  'sensor',
  'schedule',
  'user',
  'backfill',
  'partition',
] as const;

type TagBackedAttribute = (typeof TAG_BACKED_ATTRIBUTES)[number];

export const TAG_KEY_BY_ATTRIBUTE = {
  code_location: DagsterTag.RepositoryLabelTag,
  sensor: DagsterTag.SensorName,
  schedule: DagsterTag.ScheduleName,
  user: DagsterTag.User,
  backfill: DagsterTag.Backfill,
  partition: DagsterTag.Partition,
} as const satisfies Record<TagBackedAttribute, DagsterTag>;

// Mirrors the shared grammar's DIGITS and IDENTIFIER tokens, minus `*`, which is never valid here.
const UNQUOTED_VALUE_PATTERN = /^[a-zA-Z0-9_][a-zA-Z0-9_/]*$/;
const KEYWORDS = ['and', 'or', 'not'];

export const isTagBackedAttribute = (
  attribute: RunsSearchAttribute,
): attribute is TagBackedAttribute => attribute in TAG_KEY_BY_ATTRIBUTE;

export const getAttributeForTagKey = (key: string): TagBackedAttribute | null =>
  TAG_BACKED_ATTRIBUTES.find((attribute) => TAG_KEY_BY_ATTRIBUTE[attribute] === key) ?? null;

/** Quotes a value unless the shared grammar lexes it as a single bare value. */
export const formatRunsSearchValue = (value: string) => {
  if (UNQUOTED_VALUE_PATTERN.test(value) && !KEYWORDS.includes(value.toLowerCase())) {
    return value;
  }
  return `"${value}"`;
};
