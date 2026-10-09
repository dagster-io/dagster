type AssetWithLocation = {definition?: {repository: {location: {name: string}}} | null};

/**
 * Keeps the assets defined in the given code location. Assets without a definition belong to no
 * code location, so they are dropped while a code location is selected.
 */
export const filterAssetsByCodeLocation = <T extends AssetWithLocation>(
  assets: T[],
  codeLocationFilter: string | null,
): T[] =>
  codeLocationFilter
    ? assets.filter((asset) => asset.definition?.repository.location.name === codeLocationFilter)
    : assets;
