import {
  CodeLocationRowStatusType,
  CodeLocationRowType,
} from '../workspace/VirtualizedCodeLocationRow';
import {
  LocationStatusEntryFragment,
  WorkspaceLocationNodeFragment,
} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

const flatten = (
  locationStatuses: LocationStatusEntryFragment[],
  locationEntries: WorkspaceLocationNodeFragment[],
) => {
  // Consider each loaded repository to be a "code location".
  const all: CodeLocationRowType[] = [];

  const entryMap = locationEntries.reduce(
    (acc, entry) => {
      acc[entry.name] = entry;
      return acc;
    },
    {} as {[name: string]: WorkspaceLocationNodeFragment},
  );

  for (const locationStatus of locationStatuses) {
    const locationEntry = entryMap[locationStatus.name];
    let status: CodeLocationRowStatusType;

    if (locationStatus.loadStatus === 'LOADING') {
      status = 'Updating';
    } else if (locationEntry?.versionKey !== locationStatus.versionKey) {
      status = 'Loading';
    } else if (locationEntry?.locationOrLoadError?.__typename === 'PythonError') {
      status = 'Failed';
    } else {
      status = 'Loaded';
    }

    if (locationEntry?.locationOrLoadError?.__typename === 'RepositoryLocation') {
      locationEntry.locationOrLoadError.repositories.forEach((repo) => {
        all.push({
          type: 'repository' as const,
          locationStatus,
          locationEntry,
          repository: repo,
          status,
        });
      });
    } else {
      all.push({
        type: 'location' as const,
        locationStatus,
        locationEntry: locationEntry || null,
        status,
      });
    }
  }
  return all;
};

const filterRows = (
  flattened: CodeLocationRowType[],
  searchValue: string,
  filters: CodeLocationFilters,
) => {
  const queryString = searchValue.toLocaleLowerCase();
  return flattened.filter((row) => {
    if (filters.status?.length) {
      if (!filters.status.includes(row.status)) {
        return false;
      }
    }
    if (row.type !== 'repository') {
      return row.locationStatus.name.toLocaleLowerCase().includes(queryString);
    }
    return (
      row.locationStatus.name.toLocaleLowerCase().includes(queryString) ||
      row.repository.name.toLocaleLowerCase().includes(queryString)
    );
  });
};

export type CodeLocationFilters = {status: CodeLocationRowStatusType[]};

export const flattenCodeLocationRows = (
  locationStatuses: LocationStatusEntryFragment[],
  locationEntries: WorkspaceLocationNodeFragment[],
  searchValue: string = '',
  filters: CodeLocationFilters = {status: []},
) => {
  const flattened = flatten(locationStatuses, locationEntries);
  const filtered = filterRows(flattened, searchValue, filters);

  return {
    flattened,
    filtered,
  };
};
