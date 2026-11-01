/**
 * Whether app-managed component authoring is git-backed (submit opens a PR)
 * rather than writing component state live.
 *
 * Dagster+-only, so always false in open source. The Cloud app ships an
 * implementation reading the `APP_MANAGED_COMPONENTS_GIT_BACKED` feature gate —
 * the same gate the server enforces live-state writes with.
 */
export const useGitBackedComponentAuthoringEnabled = (): boolean => false;
