import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const useVisibleFeatureFlagRows = () => [
  {
    key: 'Display resources in navigation sidebar',
    flagType: FeatureFlag.flagSidebarResources,
  },
  {
    key: 'Disable WebSockets',
    flagType: FeatureFlag.flagDisableWebsockets,
  },
  {
    key: 'Disable automatically loading default config in launchpad',
    flagType: FeatureFlag.flagDisableAutoLoadDefaults,
  },
  {
    key: 'Debug console logging',
    flagType: FeatureFlag.flagDebugConsoleLogging,
  },
  {
    key: 'Revert to legacy navigation',
    label: (
      <>
        Revert to legacy navigation (
        <a
          href="https://github.com/dagster-io/dagster/discussions/21370"
          target="_blank"
          rel="noreferrer"
        >
          Learn more
        </a>
        )
      </>
    ),
    flagType: FeatureFlag.flagLegacyNav,
  },
  {
    key: 'New code location page',
    flagType: FeatureFlag.flagCodeLocationPage,
  },
  // Uncomment once we're ready for this to go live
  {
    key: 'New Runs page',
    flagType: FeatureFlag.flagRunsFeed,
    label: (
      <>
        New Runs page (
        <a
          href="https://github.com/dagster-io/dagster/discussions/24898"
          target="_blank"
          rel="noreferrer"
        >
          Learn more
        </a>
        )
      </>
    ),
  },
];
