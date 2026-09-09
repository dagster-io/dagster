/**
 * Whether a supported git provider is connected for the org, gating the
 * git-backed component authoring entry point.
 *
 * This is a Dagster+-only signal, so in open source it is always false. The
 * Cloud app ships its own implementation that checks the org's connected git
 * integration.
 */
export const useGitProviderConnected = (): boolean => false;
