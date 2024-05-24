import {CodeLocationRowType} from '../workspace/VirtualizedCodeLocationRow';
import {WorkspaceLocationNodeFragment} from '../workspace/types/WorkspaceContext.types';

const flatten = (locationEntries: WorkspaceLocationNodeFragment[]) => {
  // Consider each loaded repository to be a "code location".
  const all: CodeLocationRowType[] = [];
  for (const locationNode of locationEntries) {
    const {locationOrLoadError} = locationNode;
    if (!locationOrLoadError || locationOrLoadError?.__typename === 'PythonError') {
      all.push({type: 'error' as const, node: locationNode});
    } else {
      locationOrLoadError.repositories.forEach((repo) => {
        all.push({type: 'repository' as const, codeLocation: locationNode, repository: repo});
      });
    }
  }
  return all;
};

const filterBySearch = (flattened: CodeLocationRowType[], searchValue: string) => {
  const queryString = searchValue.toLocaleLowerCase();
  return flattened.filter((row) => {
    if (row.type === 'error') {
      return row.node.name.toLocaleLowerCase().includes(queryString);
    }
    return (
      row.codeLocation.name.toLocaleLowerCase().includes(queryString) ||
      row.repository.name.toLocaleLowerCase().includes(queryString)
    );
  });
};

export const flattenCodeLocationRows = (
  locationEntries: WorkspaceLocationNodeFragment[],
  searchValue: string = '',
) => {
  const flattened = flatten(locationEntries);
  const filtered = filterBySearch(flattened, searchValue);

  return {
    flattened,
    filtered,
  };
};
