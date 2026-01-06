import React, {useCallback, useContext, useMemo, useState} from 'react';
import {useRecoilValue} from 'recoil';

import {CodeLocationFilters, flattenCodeLocationRows} from './flattenCodeLocationRows';
import {DefinitionsSource} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {codeLocationStatusAtom} from '../nav/useCodeLocationsStatus';
import {useFilters} from '../ui/BaseFilters';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {TruncatedTextWithFullTextOnHover} from '../ui/TruncatedTextWithFullTextOnHover';
import {CodeLocationRowStatusType} from '../workspace/CodeLocationRowStatusType';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

const STATUS_VALUES: Set<string> = new Set(Object.values(CodeLocationRowStatusType));

export const useCodeLocationPageFilters = () => {
  const {loadingNonAssets: loading, locationEntries} = useContext(WorkspaceContext);
  const codeLocationStatusData = useRecoilValue(codeLocationStatusAtom);
  const [searchValue, setSearchValue] = useState('');

  const onChangeSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  const queryString = searchValue.toLocaleLowerCase();

  const [filters, setFilters] = useQueryPersistedState<CodeLocationFilters>({
    encode: ({status}) => {
      return {status: Array.isArray(status) ? status : undefined};
    },
    decode: (qs) => {
      const status = Array.isArray(qs?.status) ? qs.status : [];
      return {
        status: status.filter(
          (s) => typeof s === 'string' && STATUS_VALUES.has(s),
        ) as CodeLocationRowStatusType[],
      };
    },
  });

  const {flattened, filtered} = useMemo(() => {
    const codeLocationStatuses =
      codeLocationStatusData?.locationStatusesOrError?.__typename ===
      'WorkspaceLocationStatusEntries'
        ? codeLocationStatusData.locationStatusesOrError.entries
        : [];

    // Remove `CONNECTION` entries from the code location list.
    const codeServerEntries = new Set(
      locationEntries
        .filter((entry) => entry.definitionsSource !== DefinitionsSource.CONNECTION)
        .map((entry) => entry.name),
    );

    const filteredStatuses = codeLocationStatuses.filter((status) =>
      codeServerEntries.has(status.name),
    );
    const filteredLocationEntries = locationEntries.filter((entry) =>
      codeServerEntries.has(entry.name),
    );

    return flattenCodeLocationRows(filteredStatuses, filteredLocationEntries, queryString, filters);
  }, [locationEntries, queryString, filters, codeLocationStatusData]);

  const statusFilter = useStaticSetFilter<CodeLocationRowStatusType>({
    name: 'Status',
    icon: 'tag',
    allValues: useMemo(
      () =>
        Object.values(CodeLocationRowStatusType).map((value) => ({
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
