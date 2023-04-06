import React from 'react';
import {RecoilRoot} from 'recoil';

import {FilterDropdownButton} from './FilterDropdown';
import {FilterObject} from './useFilter';

interface UseFiltersProps {
  filters: FilterObject<any>[];
}

export const useFilters = ({filters}: UseFiltersProps) => {
  const activeFilterJsx = React.useMemo(() => {
    return filters
      .filter((filter) => filter.isActive)
      .map((filter, index) => <React.Fragment key={index}>{filter.activeJSX}</React.Fragment>);
  }, [filters]);

  return {
    button: React.useMemo(
      () => (
        <RecoilRoot>
          <FilterDropdownButton filters={filters} />
        </RecoilRoot>
      ),
      [filters],
    ),
    activeFiltersJsx: activeFilterJsx,
  };
};
