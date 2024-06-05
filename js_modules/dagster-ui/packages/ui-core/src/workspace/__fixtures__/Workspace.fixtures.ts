import {MockedResponse} from '@apollo/client/testing';

import {
  WorkspaceLocationEntry,
  WorkspaceLocationStatusEntry,
  buildWorkspaceLocationStatusEntries,
  buildWorkspaceLocationStatusEntry,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {CODE_LOCATION_STATUS_QUERY, LOCATION_WORKSPACE_QUERY} from '../WorkspaceQueries';
import {
  CodeLocationStatusQuery,
  CodeLocationStatusQueryVariables,
  LocationWorkspaceQuery,
  LocationWorkspaceQueryVariables,
} from '../types/WorkspaceQueries.types';

export const buildCodeLocationsStatusQuery = (
  entries: WorkspaceLocationStatusEntry[],
): MockedResponse => {
  return buildQueryMock<CodeLocationStatusQuery, CodeLocationStatusQueryVariables>({
    query: CODE_LOCATION_STATUS_QUERY,
    variables: {},
    data: {
      locationStatusesOrError: buildWorkspaceLocationStatusEntries({
        entries,
      }),
    },
  });
};

export const buildWorkspaceMocks = (entries: WorkspaceLocationEntry[]) => {
  return [
    ...entries.map((entry) =>
      buildQueryMock<LocationWorkspaceQuery, LocationWorkspaceQueryVariables>({
        query: LOCATION_WORKSPACE_QUERY,
        variables: {
          name: entry.name,
        },
        data: {
          workspaceLocationEntryOrError: entry,
        },
      }),
    ),
    buildCodeLocationsStatusQuery(
      entries.map((entry) =>
        buildWorkspaceLocationStatusEntry({
          ...entry,
          __typename: 'WorkspaceLocationStatusEntry',
        }),
      ),
    ),
  ];
};
