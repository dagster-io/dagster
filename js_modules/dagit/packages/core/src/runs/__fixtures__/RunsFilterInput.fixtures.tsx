import {MockedResponse} from '@apollo/client/testing';

import {WorkspaceOrError, buildPipelineTagAndValues, buildRunTags} from '../../graphql/types';
import {ROOT_WORKSPACE_QUERY} from '../../workspace/WorkspaceContext';
import {RootWorkspaceQuery} from '../../workspace/types/WorkspaceContext.types';
import {DagsterTag} from '../RunTag';
import {RUN_TAG_VALUES_QUERY} from '../RunsFilterInputNew';
import {RunTagValuesNewQuery} from '../types/RunsFilterInputNew.types';

export const buildWorkspaceContextMockedResponse = (
  workspaceOrError: WorkspaceOrError,
): MockedResponse<RootWorkspaceQuery> => ({
  request: {
    query: ROOT_WORKSPACE_QUERY,
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      workspaceOrError,
    },
  },
});

export function buildRunTagValuesQueryMockedResponse(
  tagKey: DagsterTag,
  values: string[],
): MockedResponse<RunTagValuesNewQuery> {
  return {
    request: {
      query: RUN_TAG_VALUES_QUERY,
      variables: {tagKeys: [tagKey]},
    },
    result: {
      data: {
        __typename: 'DagitQuery',
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
