import {MockedResponse} from '@apollo/client/testing';

import {
  WorkspaceLocationEntry,
  WorkspaceLocationStatusEntry,
  buildWorkspaceLocationStatusEntries,
  buildWorkspaceLocationStatusEntry,
} from '../../../graphql/types';
import {buildQueryMock} from '../../../testing/mocking';
import {CODE_LOCATION_STATUS_QUERY, LOCATION_WORKSPACE_QUERY} from '../WorkspaceQueries';
import {
  CodeLocationStatusQuery,
  CodeLocationStatusQueryVariables,
  LocationWorkspaceQuery,
  LocationWorkspaceQueryVariables,
} from '../types/WorkspaceQueries.types';

export const buildCodeLocationsStatusQuery = (
  entries: WorkspaceLocationStatusEntry[],
  options: Partial<Omit<MockedResponse, 'result' | 'query' | 'variables' | 'data'>> = {},
): MockedResponse => {
  return buildQueryMock<CodeLocationStatusQuery, CodeLocationStatusQueryVariables>({
    query: CODE_LOCATION_STATUS_QUERY,
    variables: {},
    data: {
      locationStatusesOrError: buildWorkspaceLocationStatusEntries({
        entries,
      }),
    },
    ...options,
  });
};

export const buildWorkspaceMocks = (
  entries: WorkspaceLocationEntry[],
  options: Partial<Omit<MockedResponse, 'result' | 'query' | 'variables' | 'data'>> = {},
) => {
  return [
    buildCodeLocationsStatusQuery(
      entries.map((entry) =>
        buildWorkspaceLocationStatusEntry({
          ...entry,
          updateTimestamp: entry.updatedTimestamp,
          __typename: 'WorkspaceLocationStatusEntry',
        }),
      ),
      options,
    ),
    ...entries.map((entry) =>
      buildQueryMock<LocationWorkspaceQuery, LocationWorkspaceQueryVariables>({
        query: LOCATION_WORKSPACE_QUERY,
        variables: {
          name: entry.name,
        },
        data: {
          workspaceLocationEntryOrError: entry,
        },
        ...options,
      }),
    ),
  ];
};
