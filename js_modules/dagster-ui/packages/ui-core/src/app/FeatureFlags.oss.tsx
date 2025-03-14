export enum FeatureFlag {
  flagDebugConsoleLogging = 'flagDebugConsoleLogging',
  flagDisableWebsockets = 'flagDisableWebsockets',
  flagSidebarResources = 'flagSidebarResources',
  flagDisableAutoLoadDefaults = 'flagDisableAutoLoadDefaults',
  flagLegacyRunsPage = 'flagLegacyRunsPage',
  flagSelectionSyntax = 'flagSelectionSyntax',
  flagAssetSelectionWorker = 'flagAssetSelectionWorker',
  flagAssetGraphGroupsPerCodeLocation = 'flagAssetGraphGroupsPerCodeLocation',

  // Flags for tests
  __TestFlagDefaultNone = '__TestFlagDefaultNone',
  __TestFlagDefaultTrue = '__TestFlagDefaultTrue',
  __TestFlagDefaultFalse = '__TestFlagDefaultFalse',
}
