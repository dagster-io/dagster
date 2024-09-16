import React, {useCallback, useContext, useMemo, useState} from 'react';
import {useRecoilValue} from 'recoil';

import {CodeLocationFilters, flattenCodeLocationRows} from './flattenCodeLocationRows';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {codeLocationStatusAtom} from '../nav/useCodeLocationsStatus';
import {useFilters} from '../ui/BaseFilters';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {CodeLocationRowStatusType} from '../workspace/VirtualizedCodeLocationRow';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

export const useCodeLocationPageFilters = () => {
  const {loading, locationEntries} = useContext(WorkspaceContext);
  const codeLocationStatusData = useRecoilValue(codeLocationStatusAtom);
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
    const codeLocationStatuses =
      codeLocationStatusData?.locationStatusesOrError?.__typename ===
      'WorkspaceLocationStatusEntries'
        ? codeLocationStatusData.locationStatusesOrError.entries
        : [];

    return flattenCodeLocationRows(codeLocationStatuses, locationEntries, queryString, filters);
  }, [locationEntries, queryString, filters, codeLocationStatusData]);

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
    loading,
    flattened,
    filtered,
    searchValue,
  };
};
