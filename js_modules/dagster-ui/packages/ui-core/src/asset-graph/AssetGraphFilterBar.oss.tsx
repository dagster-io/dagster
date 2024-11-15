import {Box} from '@dagster-io/ui-components';

import {FilterTag, FilterTagHighlightedText} from '../ui/BaseFilters/useFilter';

export const AssetGraphFilterBar = ({
  activeFiltersJsx,
  right,
  clearAssetSelection,
  assetSelection,
}: {
  activeFiltersJsx: JSX.Element[];
  right?: JSX.Element;
  clearAssetSelection: () => void;
  assetSelection: string;
}) => {
  if (!activeFiltersJsx.length && !assetSelection) {
    return null;
  }
  return (
    <Box
      flex={{direction: 'row', justifyContent: 'space-between', gap: 12, alignItems: 'center'}}
      padding={{vertical: 8, horizontal: 12}}
    >
      <Box flex={{gap: 12, alignItems: 'center', direction: 'row', grow: 1}}>
        {activeFiltersJsx}
        {assetSelection ? (
          <FilterTag
            label={
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                Asset selection is&nbsp;
                <FilterTagHighlightedText tooltipText={assetSelection}>
                  {assetSelection}
                </FilterTagHighlightedText>
              </Box>
            }
            onRemove={clearAssetSelection}
          />
        ) : null}
      </Box>
      {right}
    </Box>
  );
};
