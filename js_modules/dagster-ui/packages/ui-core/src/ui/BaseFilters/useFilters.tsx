import {Fragment, useCallback, useMemo} from 'react';

import {FilterDropdownButton} from './FilterDropdown';
import {FilterObject} from './useFilter';

interface UseFiltersProps {
  filters: FilterObject[];
}

export const useFilters = ({filters}: UseFiltersProps) => {
  const activeFilterJsx = useMemo(() => {
    return filters
      .filter((filter) => filter.isActive)
      .map((filter, index) => <Fragment key={index}>{filter.activeJSX}</Fragment>);
  }, [filters]);

  return {
    button: useMemo(() => <FilterDropdownButton filters={filters} />, [filters]),
    renderButton: useCallback(
      (label: string) => {
        <FilterDropdownButton filters={filters} label={label} />;
      },
      [filters],
    ),
    activeFiltersJsx: activeFilterJsx,
  };
};
