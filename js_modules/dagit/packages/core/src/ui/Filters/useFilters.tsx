import React from 'react';

import {Filter} from './Filter';
import {FilterDropdownButton} from './FilterDropdown';

interface UseFiltersProps {
  filters: Filter<any, any>[];
  activeFilters: Filter<any, any>[];
  setActiveFilters: (next: React.SetStateAction<Filter<any, any>[]>) => void;
}

export const useFilters = ({filters, activeFilters, setActiveFilters}: UseFiltersProps) => {
  React.useEffect(() => {
    filters.forEach((filter) => {
      filter.subscribe(({previousActive, active}) => {
        if (active !== previousActive) {
          if (active) {
            setActiveFilters((prev) => [...prev, filter]);
          } else {
            setActiveFilters((prev) => prev.filter((f) => f !== filter));
          }
        } else {
          setActiveFilters((prev) => [...prev]);
        }
      });
    });
  }, [filters, setActiveFilters]);

  const activeFilterJsx = React.useMemo(() => {
    return activeFilters.map((filter, index) => (
      <React.Fragment key={index}>{filter.renderActiveFilterState()}</React.Fragment>
    ));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...filters.map((filter) => filter.getState(), activeFilters)]);

  return {
    button: React.useMemo(() => <FilterDropdownButton filters={filters} />, [filters]),
    activeFiltersJsx: activeFilterJsx,
    activeFilters,
  };
};
