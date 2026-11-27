import {AppManagedComponentRepoBinding} from '../../code-location/appManagedComponentRepoBinding';

/**
 * The code location's app-managed component repo binding, or null when it has
 * none.
 *
 * Dagster+-only: returns null in open source, where components are never
 * committed to a repo. The Cloud app ships an implementation that reads the
 * binding off the deployment metadata.
 */
export const useAppManagedComponentRepoBinding = (
  _locationName: string,
): {binding: AppManagedComponentRepoBinding | null; loading: boolean} => ({
  binding: null,
  loading: false,
});
