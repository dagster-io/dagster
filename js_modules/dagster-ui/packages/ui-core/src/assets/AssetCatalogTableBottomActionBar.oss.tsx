import {Box} from '@dagster-io/ui-components';

export const AssetCatalogTableBottomActionBar = ({
  activeFiltersJsx,
}: {
  activeFiltersJsx: React.ReactNode[];
}) => {
  return activeFiltersJsx.length ? (
    <Box
      border="top-and-bottom"
      padding={{vertical: 12, left: 24, right: 12}}
      flex={{direction: 'row', gap: 4, alignItems: 'center'}}
    >
      {activeFiltersJsx}
    </Box>
  ) : null;
};
