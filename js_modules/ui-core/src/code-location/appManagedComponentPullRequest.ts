/**
 * Shared types for the git-backed "open a pull request" authoring submit.
 *
 * The hook that performs it is Dagster+-only (see
 * ``@shared/code-location/useOpenAppManagedComponentPullRequest``). These types
 * live here — outside the ``@shared`` alias — so the OSS stub, the cloud
 * implementation, and the shared authoring form all agree on one shape.
 */

export interface OpenComponentPullRequestVars {
  locationName: string;
  componentId: string;
  componentType: string;
  attributes: string;
}

export type OpenComponentPullRequestResult =
  | {
      status: 'success';
      pullRequestUrl: string;
      branchName: string;
      pullRequestNumber: number;
    }
  | {status: 'error'; message: string}
  | {status: 'unauthorized'; message: string};

export type OpenComponentPullRequestFn = (
  vars: OpenComponentPullRequestVars,
) => Promise<OpenComponentPullRequestResult>;
