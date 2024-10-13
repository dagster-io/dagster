import {Box, Heading, PageHeader, Subheading, TextInput} from '@dagster-io/ui-components';
import * as React from 'react';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {useCodeLocationPageFilters} from './useCodeLocationPageFilters';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepositoryLocationsList} from '../workspace/RepositoryLocationsList';

const SEARCH_THRESHOLD = 10;

export const CodeLocationsPageContent = () => {
  useTrackPageView();
  useDocumentTitle('Code locations');

  const {activeFiltersJsx, flattened, button, loading, filtered, onChangeSearch, searchValue} =
    useCodeLocationPageFilters();

  const entryCount = flattened.length;
  const showSearch = entryCount > SEARCH_THRESHOLD;

  const subheadingText = () => {
    if (loading || !entryCount) {
      return 'Code locations';
    }

    return entryCount === 1 ? '1 code location' : `${entryCount} code locations`;
  };

  return (
    <>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        style={{height: '64px'}}
      >
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          {button}
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
        </Box>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          {showSearch ? <div>{`${entryCount} code locations`}</div> : null}
          <ReloadAllButton />
        </Box>
      </Box>
      {activeFiltersJsx.length ? (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}} padding={{horizontal: 24}}>
          {activeFiltersJsx}
        </Box>
      ) : null}
      <RepositoryLocationsList
        loading={loading}
        codeLocations={filtered}
        isFilteredView={!!activeFiltersJsx.length}
        searchValue={searchValue}
      />
    </>
  );
};

export const CodeLocationsPage = () => {
  const {pageTitle} = React.useContext(InstancePageContext);
  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>{pageTitle}</Heading>} tabs={<InstanceTabs tab="locations" />} />
      <CodeLocationsPageContent />
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default CodeLocationsPage;
