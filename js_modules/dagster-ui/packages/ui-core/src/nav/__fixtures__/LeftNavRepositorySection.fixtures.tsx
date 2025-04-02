import {
  WorkspaceLocationEntry,
  buildAssetGroup,
  buildInstigationStates,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {INSTIGATION_STATES_QUERY} from '../InstigationStatesQuery';
import {
  InstigationStatesQuery,
  InstigationStatesQueryVariables,
} from '../types/InstigationStatesQuery.types';

const buildRepo = ({
  id,
  name,
  jobNames,
  assetGroupNames = [],
}: {
  id: string;
  name: string;
  jobNames: string[];
  assetGroupNames?: string[];
}) => {
  return buildRepository({
    id,
    name,
    pipelines: jobNames.map((jobName) =>
      buildPipeline({
        id: jobName,
        name: jobName,
      }),
    ),
    assetGroups: assetGroupNames.map((groupName) =>
      buildAssetGroup({
        groupName,
      }),
    ),
  });
};

export const buildWorkspaceQueryWithZeroLocations = () => buildWorkspaceMocks([]);

const locationEntries = [
  buildWorkspaceLocationEntry({
    id: 'ipsum-entry',
    name: 'ipsum-entry',
    locationOrLoadError: buildRepositoryLocation({
      id: 'ipsum',
      name: 'ipsum',
      repositories: [
        buildRepo({id: 'lorem', name: 'lorem', jobNames: ['my_pipeline', 'other_pipeline']}),
      ],
    }),
  }),
  buildWorkspaceLocationEntry({
    id: 'bar-entry',
    name: 'bar-entry',
    locationOrLoadError: buildRepositoryLocation({
      id: 'bar',
      name: 'bar',
      repositories: [
        buildRepo({id: 'foo', name: 'foo', jobNames: ['bar_job', 'd_job', 'e_job', 'f_job']}),
      ],
    }),
  }),
  buildWorkspaceLocationEntry({
    id: 'abc_location-entry',
    name: 'abc_location-entry',
    locationOrLoadError: buildRepositoryLocation({
      id: 'abc_location',
      name: 'abc_location',
      repositories: [
        buildRepo({
          id: 'abc_location_repo_id',
          name: DUNDER_REPO_NAME,
          jobNames: ['abc_job', 'def_job', 'ghi_job', 'jkl_job', 'mno_job', 'pqr_job'],
        }),
      ],
    }),
  }),
] as [WorkspaceLocationEntry, WorkspaceLocationEntry, WorkspaceLocationEntry];

export const buildWorkspaceQueryWithOneLocation = () => {
  return buildWorkspaceMocks([locationEntries[0]]);
};

export const buildWorkspaceQueryWithThreeLocations = () => {
  return buildWorkspaceMocks(locationEntries);
};

const entryWithOneLocationAndAssetGroup = buildWorkspaceLocationEntry({
  id: 'unique-entry',
  name: 'unique-entry',
  locationOrLoadError: buildRepositoryLocation({
    id: 'unique',
    name: 'unique',
    repositories: [
      buildRepo({
        id: 'entry',
        name: 'entry',
        jobNames: ['my_pipeline', 'other_pipeline'],
        assetGroupNames: ['my_asset_group'],
      }),
    ],
  }),
});

export const buildWorkspaceQueryWithOneLocationAndAssetGroup = () =>
  buildWorkspaceMocks([entryWithOneLocationAndAssetGroup]);

export const buildInstigationStateQueryForLocation = (locationName: string) => {
  return buildQueryMock<InstigationStatesQuery, InstigationStatesQueryVariables>({
    query: INSTIGATION_STATES_QUERY,
    variables: {
      repositoryID: locationName,
    },
    data: {
      instigationStatesOrError: buildInstigationStates({
        results: [],
      }),
    },
  });
};
