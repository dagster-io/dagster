import {Box, Button, Dialog, DialogFooter, DialogHeader, Icon} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {RepoSelector} from '../nav/RepoSelector';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

export const RepoFilterButton = () => {
  const {allRepos, visibleRepos, toggleVisible} = useContext(WorkspaceContext);
  const [open, setOpen] = useState(false);
  return (
    <>
      <Dialog
        canOutsideClickClose
        canEscapeKeyClose
        isOpen={open}
        style={{width: 'auto'}}
        onClose={() => setOpen(false)}
      >
        <DialogHeader icon="repo" label="Filter code locations" />
        <RepoSelector
          options={allRepos}
          onBrowse={() => setOpen(false)}
          onToggle={toggleVisible}
          selected={visibleRepos}
        />
        <DialogFooter>
          <Box padding={{top: 8}}>
            <Button intent="none" onClick={() => setOpen(false)}>
              Done
            </Button>
          </Box>
        </DialogFooter>
      </Dialog>

      <Button
        outlined
        icon={<Icon name="folder" />}
        rightIcon={<Icon name="expand_more" />}
        onClick={() => setOpen(true)}
      >
        {`${visibleRepos.length} of ${allRepos.length}`}
      </Button>
    </>
  );
};
