import {Box, PageHeader, Subheading, Subtitle1, TextInput} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';

import {useQuery} from '../apollo-client';
import {CODE_LOCATION_PAGE_DOCS_QUERY} from './CodeLocationsPageDocsQuery';
import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {
  CodeLocationPageDocsQuery,
  CodeLocationPageDocsQueryVariables,
} from './types/CodeLocationsPageDocsQuery.types';
import {useCodeLocationPageFilters} from './useCodeLocationPageFilters';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepositoryLocationsList} from '../workspace/RepositoryLocationsList';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

const SEARCH_THRESHOLD = 10;

export const CodeLocationsPageContent = () => {
  useTrackPageView();
  useDocumentTitle('代码位置');

  const {activeFiltersJsx, flattened, button, loading, filtered, onChangeSearch, searchValue} =
    useCodeLocationPageFilters();

  const {data} = useQuery<CodeLocationPageDocsQuery, CodeLocationPageDocsQueryVariables>(
    CODE_LOCATION_PAGE_DOCS_QUERY,
  );

  const locationsWithDocs: Set<string> = useMemo(() => {
    if (!data || data.repositoriesOrError.__typename !== 'RepositoryConnection') {
      return new Set();
    }

    const repos = data.repositoriesOrError.nodes.filter(
      (repo) => repo.__typename === 'Repository' && repo.hasLocationDocs,
    );

    return new Set(
      repos.map((repo) => {
        const repoName = repo.name;
        const locationName = repo.location.name;
        return repoAddressAsHumanString({name: repoName, location: locationName});
      }),
    );
  }, [data]);

  const entryCount = flattened.length;
  const showSearch = entryCount > SEARCH_THRESHOLD;

  const subheadingText = () => {
    if (loading || !entryCount) {
      return '代码位置';
    }

    return `${entryCount} 个代码位置`;
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
              placeholder="按名称过滤代码位置…"
              style={{width: '400px'}}
            />
          ) : (
            <Subheading id="repository-locations">{subheadingText()}</Subheading>
          )}
        </Box>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          {showSearch ? <div>{`${entryCount} 个代码位置`}</div> : null}
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
        locationsWithDocs={locationsWithDocs}
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
      <PageHeader
        title={<Subtitle1>{pageTitle}</Subtitle1>}
        tabs={<InstanceTabs tab="locations" />}
      />
      <CodeLocationsPageContent />
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default CodeLocationsPage;
