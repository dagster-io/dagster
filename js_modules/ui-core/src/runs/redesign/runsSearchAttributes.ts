import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {DagsterTag} from '../RunTag';

// Follows the legacy filter's menu order.
export const RUNS_SEARCH_ATTRIBUTES = [
  'status',
  'sensor',
  'schedule',
  'user',
  'job',
  'code_location',
  'id',
  'backfill',
  'partition',
  'tag',
  'snapshot_id',
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

// The repository tag prefix for a location's single, unnamed repository.
const SINGLE_REPOSITORY_PREFIX = `${DUNDER_REPO_NAME}@`;

// Mirrors the shared grammar's DIGITS and IDENTIFIER tokens, minus `*`, which is never valid here.
const UNQUOTED_VALUE_PATTERN = /^[a-zA-Z0-9_][a-zA-Z0-9_/]*$/;
const KEYWORDS = ['and', 'or', 'not'];

export const isTagBackedAttribute = (
  attribute: RunsSearchAttribute,
): attribute is TagBackedAttribute => attribute in TAG_KEY_BY_ATTRIBUTE;

export const getAttributeForTagKey = (key: string): TagBackedAttribute | null =>
  TAG_BACKED_ATTRIBUTES.find((attribute) => TAG_KEY_BY_ATTRIBUTE[attribute] === key) ?? null;

/** The repository tag value for a `code_location` value; without `@`, the unnamed repository. */
export const codeLocationToTagValue = (value: string) =>
  value.includes('@') ? value : `${SINGLE_REPOSITORY_PREFIX}${value}`;

/** The `code_location` value that parses back to this repository tag value, if any. */
export const tagValueToCodeLocation = (tagValue: string) => {
  if (tagValue.startsWith(SINGLE_REPOSITORY_PREFIX)) {
    const location = tagValue.slice(SINGLE_REPOSITORY_PREFIX.length);
    if (!location.includes('@')) {
      return location;
    }
  }

  // A tag value without `@` can't round-trip, since `code_location:` would add `__repository__@`.
  return tagValue.includes('@') ? tagValue : null;
};

/** The dedicated attribute and value a run tag reads as, or null for a generic `tag:` term. */
export const getAttributeTermForTag = (key: string, value: string) => {
  // Tag-backed attributes reject an empty value, so an empty value stays a generic tag.
  const attribute = value ? getAttributeForTagKey(key) : null;
  const attributeValue = attribute === 'code_location' ? tagValueToCodeLocation(value) : value;

  return attribute && attributeValue ? {attribute, value: attributeValue} : null;
};

/** Quotes a value unless the shared grammar lexes it as a single bare value. */
export const formatRunsSearchValue = (value: string) => {
  if (UNQUOTED_VALUE_PATTERN.test(value) && !KEYWORDS.includes(value.toLowerCase())) {
    return value;
  }
  return `"${value}"`;
};
