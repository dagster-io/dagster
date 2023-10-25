import {Box, Heading, PageHeader, Subheading, TextInput} from '@dagster-io/ui-components';
import * as React from 'react';

import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepositoryLocationsList} from '../workspace/RepositoryLocationsList';
import {CodeLocationRowType} from '../workspace/VirtualizedCodeLocationRow';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';

const SEARCH_THRESHOLD = 10;

export const CodeLocationsPage = () => {
  useTrackPageView();
  useDocumentTitle('Code locations');

  const {pageTitle} = React.useContext(InstancePageContext);
  const {locationEntries, loading} = React.useContext(WorkspaceContext);

  const [searchValue, setSearchValue] = React.useState('');

  const onChangeSearch = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  // Consider each loaded repository to be a "code location".
  const flattened = React.useMemo(() => {
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
  }, [locationEntries]);

  const queryString = searchValue.toLocaleLowerCase();
  const filtered = React.useMemo(() => {
    return flattened.filter((row) => {
      if (row.type === 'error') {
        return row.node.name.toLocaleLowerCase().includes(queryString);
      }
      return (
        row.codeLocation.name.toLocaleLowerCase().includes(queryString) ||
        row.repository.name.toLocaleLowerCase().includes(queryString)
      );
    });
  }, [flattened, queryString]);

  const entryCount = flattened.length;
  const showSearch = entryCount > SEARCH_THRESHOLD;

  const subheadingText = () => {
    if (loading || !entryCount) {
      return 'Code locations';
    }

    return entryCount === 1 ? '1 code location' : `${entryCount} code locations`;
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>{pageTitle}</Heading>} tabs={<InstanceTabs tab="locations" />} />
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        style={{height: '64px'}}
      >
        {showSearch ? (
          <TextInput
            icon="search"
            value={searchValue}
            onChange={onChangeSearch}
            placeholder="Filter code locations by name…"
            style={{width: '400px'}}
          />
        ) : (
          <Subheading id="repository-locations">{subheadingText()}</Subheading>
        )}
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          {showSearch ? <div>{`${entryCount} code locations`}</div> : null}
          <ReloadAllButton />
        </Box>
      </Box>
      <RepositoryLocationsList
        loading={loading}
        codeLocations={filtered}
        searchValue={searchValue}
      />
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default CodeLocationsPage;
