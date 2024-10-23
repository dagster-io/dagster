import {
  WorkspaceLocationEntry,
  buildAssetGroup,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';

const buildRepo = ({
  name,
  jobNames,
  assetGroupNames = [],
}: {
  name: string;
  jobNames: string[];
  assetGroupNames?: string[];
}) => {
  return buildRepository({
    id: name,
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
      repositories: [buildRepo({name: 'lorem', jobNames: ['my_pipeline', 'other_pipeline']})],
    }),
  }),
  buildWorkspaceLocationEntry({
    id: 'bar-entry',
    name: 'bar-entry',
    locationOrLoadError: buildRepositoryLocation({
      id: 'bar',
      name: 'bar',
      repositories: [buildRepo({name: 'foo', jobNames: ['bar_job', 'd_job', 'e_job', 'f_job']})],
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
        name: 'entry',
        jobNames: ['my_pipeline', 'other_pipeline'],
        assetGroupNames: ['my_asset_group'],
      }),
    ],
  }),
});

export const buildWorkspaceQueryWithOneLocationAndAssetGroup = () =>
  buildWorkspaceMocks([entryWithOneLocationAndAssetGroup]);
