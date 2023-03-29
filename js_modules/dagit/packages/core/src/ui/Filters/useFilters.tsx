import React from 'react';

import {Filter} from './Filter';
import {FilterDropdownButton} from './FilterDropdown';

interface UseFiltersProps {
  filters: Filter<any, any>[];
  setActiveFilters: (next: React.SetStateAction<Filter<any, any>[]>) => void;
}

export const useFilters = ({filters, setActiveFilters}: UseFiltersProps) => {
  const filterStates = React.useMemo(() => {
    return filters.map((filter) => filter.getState());
  }, [...filters.map((filter) => filter.getState())]);

  const activeFilters = React.useMemo(() => {
    return filters.filter((filter) => filter.isActive());
  }, [filterStates]);

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
  }, [activeFilters]);

  return {
    button: React.useMemo(() => <FilterDropdownButton filters={filters} />, [filters]),
    activeFiltersJsx: activeFilterJsx,
  };
};
