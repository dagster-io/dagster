import React, {useCallback, useContext, useMemo, useState} from 'react';

import {CodeLocationFilters, flattenCodeLocationRows} from './flattenCodeLocationRows';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {useFilters} from '../ui/Filters';
import {useStaticSetFilter} from '../ui/Filters/useStaticSetFilter';
import {CodeLocationRowStatusType} from '../workspace/VirtualizedCodeLocationRow';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

export const useCodeLocationPageFilters = () => {
  const workspace = useContext(WorkspaceContext);
  const [searchValue, setSearchValue] = useState('');

  const onChangeSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  const queryString = searchValue.toLocaleLowerCase();

  const [filters, setFilters] = useQueryPersistedState<CodeLocationFilters>({
    encode: ({status}) => ({
      status: status?.length ? JSON.stringify(status) : undefined,
    }),
    decode: (qs) => {
      return {
        status: qs.status ? JSON.parse(qs.status) : [],
      };
    },
  });

  const {flattened, filtered} = useMemo(() => {
    // For now don't show any items in the code location list until they are all loaded.
    // Ideally we will power this view with both location status and and location entry data.
    const locationEntries = workspace.loading ? [] : workspace.locationEntries;
    return flattenCodeLocationRows(locationEntries, queryString, filters);
  }, [workspace.loading, workspace.locationEntries, queryString, filters]);

  const statusFilter = useStaticSetFilter<CodeLocationRowStatusType>({
    name: 'Status',
    icon: 'tag',
    allValues: useMemo(
      () =>
        (['Failed', 'Loaded', 'Updating', 'Loading'] as const).map((value) => ({
          key: value,
          value,
          match: [value],
        })),
      [],
    ),
    menuWidth: '300px',
    renderLabel: ({value}) => {
      return <TruncatedTextWithFullTextOnHover text={value} />;
    },
    getStringValue: (value) => value,
    state: filters.status,
    onStateChanged: (values) => {
      setFilters({status: Array.from(values)});
    },
    matchType: 'all-of',
    canSelectAll: false,
    allowMultipleSelections: true,
  });

  const {button, activeFiltersJsx} = useFilters({filters: [statusFilter]});

  return {
    button,
    activeFiltersJsx,
    onChangeSearch,
    loading: workspace.loading,
    flattened,
    filtered,
    searchValue,
  };
};
