import {Box} from '@dagster-io/ui';
import * as React from 'react';

import {IPluginSidebarProps} from '../plugins';
import {NotebookButton} from '../ui/NotebookButton';

export const SidebarComponent: React.FC<IPluginSidebarProps> = (props) => {
  const metadata = props.definition.metadata;
  const notebookPath = metadata.find((m) => m.key === 'notebook_path');
  const repoLocName = props.repoAddress?.location;

  return (
    <Box padding={{horizontal: 16}}>
      <NotebookButton
        path={notebookPath?.value}
        repoLocation={repoLocName || ''}
        label="View Source Notebook"
      />
    </Box>
  );
};
