/**
 * Whether the viewer is looking at a branch deployment.
 *
 * Dagster+-only, so always false in open source.
 */
export const useIsBranchDeployment = (): boolean => false;
