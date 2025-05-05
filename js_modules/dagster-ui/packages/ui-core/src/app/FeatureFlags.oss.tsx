export enum FeatureFlag {
  flagDebugConsoleLogging = 'flagDebugConsoleLogging',
  flagDisableWebsockets = 'flagDisableWebsockets',
  flagSidebarResources = 'flagSidebarResources',
  flagDisableAutoLoadDefaults = 'flagDisableAutoLoadDefaults',
  flagAssetSelectionWorker = 'flagAssetSelectionWorker',
  flagAssetNodeFacets = 'flagAssetNodeFacets',
  flagUseNewObserveUIs = 'flagUseNewObserveUIs',
  flagMarketplace = 'flagMarketplace',
  flagDocsInApp = 'flagDocsInApp',

  // Flags for tests
  __TestFlagDefaultNone = '__TestFlagDefaultNone',
  __TestFlagDefaultTrue = '__TestFlagDefaultTrue',
  __TestFlagDefaultFalse = '__TestFlagDefaultFalse',
}
