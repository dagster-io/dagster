import {Box, Heading, PageHeader, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {useTrackPageView} from '../app/analytics';
import {ReloadAllButton} from '../workspace/ReloadAllButton';
import {RepositoryLocationsList} from '../workspace/RepositoryLocationsList';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';

export const CodeLocationsPage = () => {
  useTrackPageView();

  const {pageTitle} = React.useContext(InstancePageContext);
  const {locationEntries, loading} = React.useContext(WorkspaceContext);
  const entryCount = locationEntries.length;

  const subheadingText = () => {
    if (loading || !entryCount) {
      return 'Code locations';
    }
    return entryCount === 1 ? '1 code location' : `${entryCount} code locations`;
  };

  return (
    <>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="code-locations" />}
      />
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        style={{height: '64px'}} // Preserve height whether "Reload all" is present or not
      >
        <Subheading id="repository-locations">{subheadingText()}</Subheading>
        {entryCount > 1 ? <ReloadAllButton /> : null}
      </Box>
      <RepositoryLocationsList />
    </>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default CodeLocationsPage;
