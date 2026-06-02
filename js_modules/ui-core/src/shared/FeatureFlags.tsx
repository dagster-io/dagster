export enum FeatureFlag {
  flagDebugConsoleLogging = 'flagDebugConsoleLogging',
  flagDisableWebsockets = 'flagDisableWebsockets',
  flagDisableAutoLoadDefaults = 'flagDisableAutoLoadDefaults',
  flagAssetGraphGroupsPerCodeLocation = 'flagAssetGraphGroupsPerCodeLocation',
  flagSkipOptionalResourceDefaultsInRunConfig = 'flagSkipOptionalResourceDefaultsInRunConfig',
  flagComponentInstanceUI = 'flagComponentInstanceUI',

  // Flags for tests
  __TestFlagDefaultNone = '__TestFlagDefaultNone',
  __TestFlagDefaultTrue = '__TestFlagDefaultTrue',
  __TestFlagDefaultFalse = '__TestFlagDefaultFalse',
}
