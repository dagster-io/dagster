/**
 * Whether the app-managed (UI-backed) component instance UI is available.
 *
 * This is a Dagster+-only feature, so in open source it is always disabled.
 * The Cloud app ships its own implementation of this hook, gated behind the
 * experimental `flagComponentInstanceUI` feature flag.
 */
export const useComponentInstanceUIEnabled = (): boolean => false;
