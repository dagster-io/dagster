import {useCallback, useMemo} from 'react';

import {RUN_TAG_KEYS_QUERY, RUN_TAG_VALUES_QUERY} from './RunTagQueries';
import {useLazyQuery} from '../apollo-client';
import {
  RunTagKeysQuery,
  RunTagKeysQueryVariables,
  RunTagValuesQuery,
  RunTagValuesQueryVariables,
} from './types/RunTagQueries.types';
import {COMMON_COLLATOR} from '../app/Util';

const sortValues = (values: string[]) => [...values].sort(COMMON_COLLATOR.compare);

/** Loads and sorts run tag keys when `fetch` is called. */
export const useLazyRunTagKeys = () => {
  const [fetch, {data, loading}] = useLazyQuery<RunTagKeysQuery, RunTagKeysQueryVariables>(
    RUN_TAG_KEYS_QUERY,
  );
  const keys = useMemo(
    () =>
      data?.runTagKeysOrError?.__typename === 'RunTagKeys'
        ? sortValues(data.runTagKeysOrError.keys)
        : [],
    [data],
  );

  return {fetch, keys, loading};
};

/** Sorted values from a run tag values query result; empty on error. */
export const getSortedRunTagValues = (data: RunTagValuesQuery | undefined) =>
  data?.runTagsOrError?.__typename === 'RunTags'
    ? sortValues(data.runTagsOrError.tags.flatMap((tag) => tag.values))
    : [];

/** Loads and sorts the values for a run tag key when `fetch` is called. */
export const useLazyRunTagValues = (tagKey: string) => {
  const [execute, {data, loading}] = useLazyQuery<RunTagValuesQuery, RunTagValuesQueryVariables>(
    RUN_TAG_VALUES_QUERY,
  );
  const fetch = useCallback(() => execute({variables: {tagKeys: [tagKey]}}), [execute, tagKey]);
  const values = useMemo(() => getSortedRunTagValues(data), [data]);

  return {
    fetch,
    values,
    /** True once a request has returned the tag values. */
    loaded: data?.runTagsOrError?.__typename === 'RunTags',
    loading,
  };
};
