import {
  Button,
  Dialog,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Popover,
  StyledReadOnlyCodeMirror,
} from '@dagster-io/ui';
import * as React from 'react';
import * as yaml from 'yaml';

import {WorkspaceRepositoryLocationNode} from './WorkspaceContext';

export const CodeLocationMenu: React.FC<{locationNode: WorkspaceRepositoryLocationNode}> = ({
  locationNode,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  return (
    <>
      <Popover
        position="bottom-left"
        content={
          <Menu>
            <MenuItem icon="info" text="View configuration" onClick={() => setIsOpen(true)} />
          </Menu>
        }
      >
        <Button icon={<Icon name="expand_more" />}></Button>
      </Popover>
      <CodeLocationConfigDialog
        metadata={locationNode.displayMetadata}
        isOpen={isOpen}
        setIsOpen={setIsOpen}
      />
    </>
  );
};

export const CodeLocationConfigDialog: React.FC<{
  isOpen: boolean;
  setIsOpen: (next: boolean) => void;
  metadata: WorkspaceRepositoryLocationNode['displayMetadata'];
}> = ({isOpen, setIsOpen, metadata}) => {
  return (
    <Dialog
      title="Code location configuration"
      icon="info"
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      style={{width: '600px'}}
    >
      <CodeLocationConfig displayMetadata={metadata} />
      <DialogFooter topBorder>
        <Button onClick={() => setIsOpen(false)} intent="primary">
          Done
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const CodeLocationConfig: React.FC<{
  displayMetadata: WorkspaceRepositoryLocationNode['displayMetadata'];
}> = ({displayMetadata}) => {
  const yamlString = React.useMemo(() => {
    const kvPairs = displayMetadata.reduce((accum, item) => {
      return {...accum, [item.key]: item.value};
    }, {});
    return yaml.stringify(kvPairs);
  }, [displayMetadata]);

  return (
    <StyledReadOnlyCodeMirror
      value={yamlString}
      options={{lineNumbers: true, mode: 'yaml'}}
      theme={['config-editor']}
    />
  );
};
