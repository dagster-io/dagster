/**
 * Shared type for a code location's app-managed component repo binding — where
 * UI-authored components are committed.
 *
 * The hook that reads it is Dagster+-only (see
 * ``@shared/code-location/useAppManagedComponentRepoBinding``). This type lives
 * outside the ``@shared`` alias so the OSS stub, the cloud implementation, and
 * the shared components page all agree on one shape.
 */
export interface AppManagedComponentRepoBinding {
  provider: string;
  repoOwner: string;
  repoName: string;
  baseBranch: string;
  defsBasePath: string;
  /** Reported by the location's last deploy, so it can't be edited by hand. */
  isFromDeploy: boolean;
  /** Set by hand, but pointing away from the repo the location deploys from. */
  divergesFromDeployedRepo: boolean;
  deployedRepoUrl: string | null;
}
