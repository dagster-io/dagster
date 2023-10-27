import React from 'react';

import {FilterDropdownButton} from './FilterDropdown';
import {FilterObject} from './useFilter';

interface UseFiltersProps {
  filters: FilterObject[];
}

export const useFilters = ({filters}: UseFiltersProps) => {
  const activeFilterJsx = React.useMemo(() => {
    return filters
      .filter((filter) => filter.isActive)
      .map((filter, index) => <React.Fragment key={index}>{filter.activeJSX}</React.Fragment>);
  }, [filters]);

  return {
    button: React.useMemo(() => <FilterDropdownButton filters={filters} />, [filters]),
    activeFiltersJsx: activeFilterJsx,
  };
};
