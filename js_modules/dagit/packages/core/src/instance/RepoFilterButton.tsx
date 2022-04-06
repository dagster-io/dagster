import {Box, Button, DialogFooter, DialogHeader, Dialog, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {RepoSelector} from '../nav/RepoSelector';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

export const RepoFilterButton: React.FC = () => {
  const {allRepos, visibleRepos, toggleVisible} = React.useContext(WorkspaceContext);
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <Dialog
        canOutsideClickClose
        canEscapeKeyClose
        isOpen={open}
        style={{width: 'auto'}}
        onClose={() => setOpen(false)}
      >
        <DialogHeader icon="repo" label="Repositories" />
        <div>
          <Box padding={{vertical: 8, horizontal: 24}}>
            {`${visibleRepos.length} of ${allRepos.length} selected`}
          </Box>
          <RepoSelector
            options={allRepos}
            onBrowse={() => setOpen(false)}
            onToggle={toggleVisible}
            selected={visibleRepos}
          />
        </div>
        <DialogFooter>
          <Box padding={{top: 8}}>
            <Button intent="none" onClick={() => setOpen(false)}>
              Done
            </Button>
          </Box>
        </DialogFooter>
      </Dialog>

      <Button
        icon={<Icon name="folder" />}
        rightIcon={<Icon name="expand_more" />}
        onClick={() => setOpen(true)}
      >
        {`${visibleRepos.length} of ${allRepos.length} Repositories`}
      </Button>
    </>
  );
};
