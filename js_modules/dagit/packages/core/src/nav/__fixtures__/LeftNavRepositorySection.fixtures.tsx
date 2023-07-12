import {MockedResponse} from '@apollo/client/testing';

import {
  buildAssetGroup,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspace,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {ROOT_WORKSPACE_QUERY} from '../../workspace/WorkspaceContext';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {RootWorkspaceQuery} from '../../workspace/types/WorkspaceContext.types';

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

export const buildWorkspaceQueryWithZeroLocations = (): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [],
        }),
      },
    },
  };
};

export const buildWorkspaceQueryWithOneLocation = (): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              id: 'ipsum-entry',
              name: 'ipsum-entry',
              locationOrLoadError: buildRepositoryLocation({
                id: 'ipsum',
                name: 'ipsum',
                repositories: [
                  buildRepo({name: 'lorem', jobNames: ['my_pipeline', 'other_pipeline']}),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};

export const buildWorkspaceQueryWithThreeLocations = (): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              id: 'ipsum-entry',
              name: 'ipsum-entry',
              locationOrLoadError: buildRepositoryLocation({
                id: 'ipsum',
                name: 'ipsum',
                repositories: [
                  buildRepo({name: 'lorem', jobNames: ['my_pipeline', 'other_pipeline']}),
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
                  buildRepo({name: 'foo', jobNames: ['bar_job', 'd_job', 'e_job', 'f_job']}),
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
                    name: DUNDER_REPO_NAME,
                    jobNames: ['abc_job', 'def_job', 'ghi_job', 'jkl_job', 'mno_job', 'pqr_job'],
                  }),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};

export const buildWorkspaceQueryWithOneLocationAndAssetGroup = (): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              id: 'ipsum-entry',
              name: 'ipsum-entry',
              locationOrLoadError: buildRepositoryLocation({
                id: 'ipsum',
                name: 'ipsum',
                repositories: [
                  buildRepo({
                    name: 'lorem',
                    jobNames: ['my_pipeline', 'other_pipeline'],
                    assetGroupNames: ['my_asset_group'],
                  }),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};
