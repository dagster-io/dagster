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
    key: 'Revert to legacy Runs page',
    flagType: FeatureFlag.flagLegacyRunsPage,
    label: (
      <>
        Revert to legacy Runs page (
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
  {
    key: 'Enable new selection syntax for Asset/Op/Run graphs',
    flagType: FeatureFlag.flagSelectionSyntax,
    label: (
      <>
        Enable new selection syntax for Asset/Op/Run graphs (
        <a
          href="https://github.com/dagster-io/dagster/discussions/26849"
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
