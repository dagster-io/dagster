import {__ANONYMOUS_ASSET_JOB_PREFIX} from '../../asset-graph/Utils';
import {
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';

export const workspaceWithJob = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    name: 'some_workspace',
    locationOrLoadError: buildRepositoryLocation({
      name: 'location_with_job',
      repositories: [
        buildRepository({
          name: 'repo_with_job',
          pipelines: [
            buildPipeline({
              name: 'some_job',
              isJob: true,
            }),
          ],
        }),
      ],
    }),
  }),
]);

export const workspaceWithNoJobs = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    name: 'some_workspace',
    locationOrLoadError: buildRepositoryLocation({
      name: 'location_without_job',
      repositories: [
        buildRepository({
          name: 'repo_without_job',
          pipelines: [],
        }),
      ],
    }),
  }),
]);

export const workspaceWithDunderJob = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    name: 'some_workspace',
    locationOrLoadError: buildRepositoryLocation({
      name: 'location_without_job',
      repositories: [
        buildRepository({
          name: `${__ANONYMOUS_ASSET_JOB_PREFIX}_pseudo_job`,
          pipelines: [],
        }),
      ],
    }),
  }),
]);
