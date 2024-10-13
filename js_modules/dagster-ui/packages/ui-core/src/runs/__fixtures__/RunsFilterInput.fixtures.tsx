import {MockedResponse} from '@apollo/client/testing';

import {buildPipelineTagAndValues, buildRunTags} from '../../graphql/types';
import {DagsterTag} from '../RunTag';
import {RUN_TAG_VALUES_QUERY} from '../RunsFilterInput';
import {RunTagValuesQuery} from '../types/RunsFilterInput.types';

export function buildRunTagValuesQueryMockedResponse(
  tagKey: DagsterTag,
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
