import {Box, ButtonWIP, DialogFooter, DialogHeader, DialogWIP, IconWIP} from '@dagster-io/ui';
import * as React from 'react';

import {RepoSelector} from '../nav/RepoSelector';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

export const RepoFilterButton: React.FunctionComponent = () => {
  const {allRepos, visibleRepos, toggleVisible} = React.useContext(WorkspaceContext);
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <DialogWIP
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
            <ButtonWIP intent="none" onClick={() => setOpen(false)}>
              Done
            </ButtonWIP>
          </Box>
        </DialogFooter>
      </DialogWIP>

      <ButtonWIP
        icon={<IconWIP name="folder" />}
        rightIcon={<IconWIP name="expand_more" />}
        onClick={() => setOpen(true)}
      >
        {`${visibleRepos.length} of ${allRepos.length} Repositories`}
      </ButtonWIP>
    </>
  );
};
