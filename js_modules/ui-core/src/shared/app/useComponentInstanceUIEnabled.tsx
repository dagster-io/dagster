/**
 * Whether the app-managed (UI-backed) component instance UI is available.
 *
 * This is a Dagster+-only feature, so in open source it is always disabled.
 * The Cloud app ships its own implementation of this hook, gated behind the
 * experimental `flagComponentInstanceUI` feature flag.
 *
 * `NEXT_PUBLIC_DAGSTER_DEV_ENABLE_APP_MANAGED_COMPONENTS` is a
 * local-development override used to exercise the authoring form against
 * `dg dev`. Next inlines it at build time, so shipped open-source bundles --
 * which are built without it -- always evaluate this to `false`. It is not a
 * supported way to enable the feature.
 */
export const useComponentInstanceUIEnabled = (): boolean =>
  process.env.NEXT_PUBLIC_DAGSTER_DEV_ENABLE_APP_MANAGED_COMPONENTS === '1';
