import {OpenComponentPullRequestFn} from '../../code-location/appManagedComponentPullRequest';

/**
 * Git-backed "open a pull request" authoring submit.
 *
 * Dagster+-only: returns ``null`` in open source, where the authoring form keeps
 * writing component state directly. The Cloud app ships an implementation that
 * opens a PR via the ``openAppManagedComponentPullRequest`` mutation.
 */
export const useOpenAppManagedComponentPullRequest = (): OpenComponentPullRequestFn | null => null;
