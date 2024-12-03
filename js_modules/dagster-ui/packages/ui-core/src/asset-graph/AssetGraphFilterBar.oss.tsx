import {Box} from '@dagster-io/ui-components';
import {useCallback} from 'react';

import {FilterTag, FilterTagHighlightedText} from '../ui/BaseFilters/useFilter';

export const AssetGraphFilterBar = ({
  activeFiltersJsx,
  right,
  assetSelection,
  setAssetSelection,
}: {
  activeFiltersJsx: JSX.Element[];
  right?: JSX.Element;
  assetSelection: string;
  setAssetSelection: (selection: string) => void;
}) => {
  const clearAssetSelection = useCallback(() => {
    setAssetSelection('');
  }, [setAssetSelection]);
  if (!activeFiltersJsx.length && !assetSelection) {
    return null;
  }
  return (
    <Box
      flex={{direction: 'row', justifyContent: 'space-between', gap: 12, alignItems: 'center'}}
      padding={{vertical: 8, horizontal: 12}}
      border="top"
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
