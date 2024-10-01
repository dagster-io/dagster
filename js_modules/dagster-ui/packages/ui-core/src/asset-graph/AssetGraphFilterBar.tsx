import {Box} from '@dagster-io/ui-components';

import {FilterTag, FilterTagHighlightedText} from '../ui/BaseFilters/useFilter';

export const AssetGraphFilterBar = ({
  activeFiltersJsx,
  right,
  explorerPath,
  clearExplorerPath,
}: {
  activeFiltersJsx: JSX.Element[];
  right?: JSX.Element;
  clearExplorerPath: () => void;
  explorerPath: string;
}) => {
  if (!activeFiltersJsx.length && !explorerPath) {
    return null;
  }
  return (
    <Box
      flex={{direction: 'row', justifyContent: 'space-between', gap: 12, alignItems: 'center'}}
      padding={{vertical: 8, horizontal: 12}}
    >
      <Box flex={{gap: 12, alignItems: 'center', direction: 'row', grow: 1}}>
        {activeFiltersJsx}
        {explorerPath ? (
          <FilterTag
            label={
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                Asset selection is&nbsp;
                <FilterTagHighlightedText tooltipText={explorerPath}>
                  {explorerPath}
                </FilterTagHighlightedText>
              </Box>
            }
            onRemove={clearExplorerPath}
          />
        ) : null}
      </Box>
      {right}
    </Box>
  );
};
