export enum FeatureFlag {
  flagDebugConsoleLogging = 'flagDebugConsoleLogging',
  flagDisableWebsockets = 'flagDisableWebsockets',
  flagSidebarResources = 'flagSidebarResources',
  flagDisableAutoLoadDefaults = 'flagDisableAutoLoadDefaults',
  flagAssetNodeFacets = 'flagAssetNodeFacets',
  flagUseNewObserveUIs = 'flagUseNewObserveUIs',
  flagMarketplace = 'flagMarketplace',
  flagAssetGraphGroupsPerCodeLocation = 'flagAssetGraphGroupsPerCodeLocation',
  flagNavigationUpdate = 'flagNavigationUpdate',
  flagAssetCatalogSidebar = 'flagAssetCatalogSidebar',

  // Flags for tests
  __TestFlagDefaultNone = '__TestFlagDefaultNone',
  __TestFlagDefaultTrue = '__TestFlagDefaultTrue',
  __TestFlagDefaultFalse = '__TestFlagDefaultFalse',
}
