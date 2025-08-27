import {Box, Tab, Tabs, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {CODE_LOCATION_HAS_DOCS_QUERY} from './CodeLocationHasDocsQuery';
import {findRepositoryInLocation} from './findRepositoryInLocation';
import {useQuery} from '../apollo-client';
import {TabLink} from '../ui/TabLink';
import {WorkspaceLocationNodeFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {
  CodeLocationHasDocsQuery,
  CodeLocationHasDocsQueryVariables,
} from './types/CodeLocationHasDocsQuery.types';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';

export type CodeLocationTabType = 'overview' | 'docs' | 'definitions';

interface Props {
  repoAddress: RepoAddress;
  selectedTab: CodeLocationTabType;
  locationEntry: WorkspaceLocationNodeFragment | null;
}

export const CodeLocationTabs = (props: Props) => {
  const {repoAddress, selectedTab, locationEntry} = props;

  const {data} = useQuery<CodeLocationHasDocsQuery, CodeLocationHasDocsQueryVariables>(
    CODE_LOCATION_HAS_DOCS_QUERY,
    {
      variables: {
        repositorySelector: repoAddressToSelector(repoAddress),
      },
      fetchPolicy: 'cache-first',
    },
  );

  const hasDocs = useMemo(() => {
    return (
      data?.repositoryOrError.__typename === 'Repository' && data.repositoryOrError.hasLocationDocs
    );
  }, [data]);

  const repository = useMemo(
    () => findRepositoryInLocation(locationEntry, repoAddress),
    [locationEntry, repoAddress],
  );

  return (
    <Tabs selectedTabId={selectedTab}>
      <TabLink id="overview" title="Overview" to={workspacePathFromAddress(repoAddress, '/')} />
      {hasDocs ? (
        <TabLink
          id="docs"
          title={
            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
              <span>Docs</span>
              <Tag>
                <span style={{fontWeight: 'normal'}}>Beta</span>
              </Tag>
            </Box>
          }
          to={workspacePathFromAddress(repoAddress, '/docs')}
        />
      ) : null}
      {repository ? (
        <TabLink
          id="definitions"
          title="Definitions"
          to={workspacePathFromAddress(repoAddress, '/definitions')}
        />
      ) : (
        <Tab id="definitions" title="Definitions" disabled />
      )}
    </Tabs>
  );
};
