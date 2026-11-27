import {MockedResponse} from '@apollo/client/testing';

import {buildPipelineTagAndValues, buildRunTagKeys, buildRunTags} from '../../graphql/builders';
import {DagsterTag} from '../RunTag';
import {RUN_TAG_KEYS_QUERY, RUN_TAG_VALUES_QUERY} from '../RunTagQueries';
import {RunTagKeysQuery, RunTagValuesQuery} from '../types/RunTagQueries.types';

// The tags whose values the Runs filter and search load when they gain focus.
const FOCUS_TAG_KEYS = [
  DagsterTag.SensorName,
  DagsterTag.ScheduleName,
  DagsterTag.User,
  DagsterTag.Backfill,
  DagsterTag.Partition,
] as const;

type RunTagFocusMocksOptions = {
  tagKeys?: string[];
  values?: Partial<Record<(typeof FOCUS_TAG_KEYS)[number], string[]>>;
};

export function buildRunTagValuesQueryMockedResponse(
  tagKey: string,
  values: string[],
): MockedResponse<RunTagValuesQuery> {
  return {
    request: {
      query: RUN_TAG_VALUES_QUERY,
      variables: {tagKeys: [tagKey]},
    },
    result: {
      data: {
        __typename: 'Query',
        runTagsOrError: buildRunTags({
          tags: [
            buildPipelineTagAndValues({
              key: tagKey,
              values,
            }),
          ],
        }),
      },
    },
  };
}

export function buildRunTagKeysQueryMockedResponse(
  keys: string[],
): MockedResponse<RunTagKeysQuery> {
  return {
    request: {
      query: RUN_TAG_KEYS_QUERY,
    },
    result: {
      data: {
        __typename: 'Query',
        runTagKeysOrError: buildRunTagKeys({keys}),
      },
    },
  };
}

/** Mocks for the run tag queries fired when the Runs filter or search gains focus. */
export function buildRunTagFocusMocks({
  tagKeys = [],
  values = {},
}: RunTagFocusMocksOptions = {}): MockedResponse[] {
  return [
    buildRunTagKeysQueryMockedResponse(tagKeys),
    ...FOCUS_TAG_KEYS.map((tagKey) =>
      buildRunTagValuesQueryMockedResponse(tagKey, values[tagKey] ?? []),
    ),
  ];
}
