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
import {DagsterRepoOption} from '../../workspace/WorkspaceContext/util';
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

const loremRepo = buildRepo({
  id: 'lorem',
  name: 'lorem',
  jobNames: ['my_pipeline', 'other_pipeline'],
});

const ipsumLocation = buildRepositoryLocation({
  id: 'ipsum',
  name: 'ipsum',
  repositories: [loremRepo],
});

export const loremIpsumOption: DagsterRepoOption = {
  repository: loremRepo,
  repositoryLocation: ipsumLocation,
};

const fooRepo = buildRepo({
  id: 'foo',
  name: 'foo',
  jobNames: ['bar_job', 'd_job', 'e_job', 'f_job'],
});

const barLocation = buildRepositoryLocation({
  id: 'bar',
  name: 'bar',
  repositories: [fooRepo],
});

export const fooBarOption: DagsterRepoOption = {
  repository: fooRepo,
  repositoryLocation: barLocation,
};

const abcRepo = buildRepo({
  id: 'abc_location_repo_id',
  name: DUNDER_REPO_NAME,
  jobNames: ['abc_job', 'def_job', 'ghi_job', 'jkl_job', 'mno_job', 'pqr_job'],
});

const abcLocation = buildRepositoryLocation({
  id: 'abc_location',
  name: 'abc_location',
  repositories: [abcRepo],
});

export const abcLocationOption: DagsterRepoOption = {
  repository: abcRepo,
  repositoryLocation: abcLocation,
};

const entryRepo = buildRepo({
  id: 'entry',
  name: 'entry',
  jobNames: ['my_pipeline', 'other_pipeline'],
  assetGroupNames: ['my_asset_group'],
});

const uniqueLocation = buildRepositoryLocation({
  id: 'unique',
  name: 'unique',
  repositories: [entryRepo],
});

export const uniqueOption: DagsterRepoOption = {
  repository: entryRepo,
  repositoryLocation: uniqueLocation,
};

const locationEntries = () =>
  [
    buildWorkspaceLocationEntry({
      id: 'ipsum',
      name: 'ipsum',
      locationOrLoadError: buildRepositoryLocation({
        id: 'ipsum',
        name: 'ipsum',
        repositories: [
          buildRepo({id: 'lorem', name: 'lorem', jobNames: ['my_pipeline', 'other_pipeline']}),
        ],
      }),
    }),
    buildWorkspaceLocationEntry({
      id: 'bar',
      name: 'bar',
      locationOrLoadError: buildRepositoryLocation({
        id: 'bar',
        name: 'bar',
        repositories: [
          buildRepo({id: 'foo', name: 'foo', jobNames: ['bar_job', 'd_job', 'e_job', 'f_job']}),
        ],
      }),
    }),
    buildWorkspaceLocationEntry({
      id: 'abc_location',
      name: 'abc_location',
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
  return buildWorkspaceMocks([locationEntries()[0]]);
};

export const buildWorkspaceQueryWithThreeLocations = () => {
  return buildWorkspaceMocks(locationEntries());
};

const entryWithOneLocationAndAssetGroup = () =>
  buildWorkspaceLocationEntry({
    id: 'unique',
    name: 'unique',
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
  buildWorkspaceMocks([entryWithOneLocationAndAssetGroup()]);

export const buildInstigationStateQueryForLocation = (repoId: string) => {
  return buildQueryMock<InstigationStatesQuery, InstigationStatesQueryVariables>({
    query: INSTIGATION_STATES_QUERY,
    variables: {
      repositoryID: repoId,
    },
    data: {
      instigationStatesOrError: buildInstigationStates({
        results: [],
      }),
    },
    maxUsageCount: 1000,
  });
};
