import {Box, NonIdealState, Spinner, Table} from '@dagster-io/ui';
import * as React from 'react';

import {CodeLocationRowSet} from './CodeLocationRowSet';
import {WorkspaceContext} from './WorkspaceContext';

export const RepositoryLocationsList = () => {
  const {locationEntries, loading} = React.useContext(WorkspaceContext);

  if (loading && !locationEntries.length) {
    return (
      <Box flex={{gap: 8, alignItems: 'center'}} padding={{horizontal: 24}}>
        <Spinner purpose="body-text" />
        <div>Loading...</div>
      </Box>
    );
  }

  if (!locationEntries.length) {
    return (
      <Box padding={{vertical: 32}}>
        <NonIdealState
          icon="folder"
          title="No code locations"
          description="When you add a code location, your definitions will appear here."
        />
      </Box>
    );
  }

  return (
    <Table $monospaceFont={false}>
      <thead>
        <tr>
          <th>Name</th>
          <th>Status</th>
          <th>Updated</th>
          <th>Definitions</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {locationEntries.map((location) => (
          <CodeLocationRowSet key={location.name} locationNode={location} />
        ))}
      </tbody>
    </Table>
  );
};
