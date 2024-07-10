import {
  CodeLocationRowStatusType,
  CodeLocationRowType,
} from '../workspace/VirtualizedCodeLocationRow';
import {WorkspaceLocationNodeFragment} from '../workspace/types/WorkspaceQueries.types';

const flatten = (locationEntries: WorkspaceLocationNodeFragment[]) => {
  // Consider each loaded repository to be a "code location".
  const all: CodeLocationRowType[] = [];
  for (const locationNode of locationEntries) {
    const {locationOrLoadError} = locationNode;
    let status: CodeLocationRowStatusType;
    if (locationNode.loadStatus === 'LOADING') {
      if (locationOrLoadError) {
        status = 'Updating';
      } else {
        status = 'Loading';
      }
    } else {
      if (locationOrLoadError?.__typename === 'PythonError') {
        status = 'Failed';
      } else {
        status = 'Loaded';
      }
    }
    if (!locationOrLoadError || locationOrLoadError?.__typename === 'PythonError') {
      all.push({type: 'error' as const, node: locationNode, status});
    } else {
      locationOrLoadError.repositories.forEach((repo) => {
        all.push({
          type: 'repository' as const,
          codeLocation: locationNode,
          repository: repo,
          status,
        });
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
    if (row.type === 'error') {
      return row.node.name.toLocaleLowerCase().includes(queryString);
    }
    return (
      row.codeLocation.name.toLocaleLowerCase().includes(queryString) ||
      row.repository.name.toLocaleLowerCase().includes(queryString)
    );
  });
};

export type CodeLocationFilters = Partial<{status: CodeLocationRowStatusType[]}>;

export const flattenCodeLocationRows = (
  locationEntries: WorkspaceLocationNodeFragment[],
  searchValue: string = '',
  filters: CodeLocationFilters = {},
) => {
  const flattened = flatten(locationEntries);
  const filtered = filterRows(flattened, searchValue, filters);

  return {
    flattened,
    filtered,
  };
};
