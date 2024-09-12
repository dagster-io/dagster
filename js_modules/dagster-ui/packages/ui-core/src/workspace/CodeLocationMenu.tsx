import {
  Button,
  Dialog,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Popover,
  StyledRawCodeMirror,
  Table,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import * as yaml from 'yaml';

import {WorkspaceRepositoryLocationNode} from './WorkspaceContext/WorkspaceContext';

export const CodeLocationMenu = ({
  locationNode,
}: {
  locationNode: WorkspaceRepositoryLocationNode;
}) => {
  const [configIsOpen, setConfigIsOpen] = useState(false);
  const [libsIsOpen, setLibsIsOpen] = useState(false);

  let libsMenuItem = null;
  let libsDialog = null;
  if (
    locationNode.locationOrLoadError?.__typename === 'RepositoryLocation' &&
    locationNode.locationOrLoadError.dagsterLibraryVersions !== null
  ) {
    libsMenuItem = (
      <MenuItem icon="info" text="View Dagster libraries" onClick={() => setLibsIsOpen(true)} />
    );
    libsDialog = (
      <DagsterLibrariesDialog
        libraries={locationNode.locationOrLoadError.dagsterLibraryVersions}
        isOpen={libsIsOpen}
        setIsOpen={setLibsIsOpen}
      />
    );
  }

  return (
    <>
      <Popover
        position="bottom-left"
        content={
          <Menu>
            <MenuItem icon="info" text="View configuration" onClick={() => setConfigIsOpen(true)} />
            {libsMenuItem}
          </Menu>
        }
      >
        <Button icon={<Icon name="expand_more" />}></Button>
      </Popover>
      <CodeLocationConfigDialog
        metadata={locationNode.displayMetadata}
        isOpen={configIsOpen}
        setIsOpen={setConfigIsOpen}
      />
      {libsDialog}
    </>
  );
};

export const CodeLocationConfigDialog = ({
  isOpen,
  setIsOpen,
  metadata,
}: {
  isOpen: boolean;
  setIsOpen: (next: boolean) => void;
  metadata: WorkspaceRepositoryLocationNode['displayMetadata'];
}) => {
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

export const DagsterLibrariesDialog = ({
  isOpen,
  setIsOpen,
  libraries,
}: {
  isOpen: boolean;
  setIsOpen: (next: boolean) => void;
  libraries: {name: string; version: string}[];
}) => {
  return (
    <Dialog
      title="Dagster library versions"
      icon="info"
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      style={{width: '600px'}}
    >
      <Table>
        <thead>
          <tr>
            <th>Library</th>
            <th>Version</th>
          </tr>
        </thead>
        <tbody>
          {libraries.map((library) => (
            <tr key={library.name}>
              <td>{library.name}</td>
              <td>{library.version}</td>
            </tr>
          ))}
        </tbody>
      </Table>
      <DialogFooter topBorder>
        <Button onClick={() => setIsOpen(false)} intent="primary">
          Done
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const CodeLocationConfig = ({
  displayMetadata,
}: {
  displayMetadata: WorkspaceRepositoryLocationNode['displayMetadata'];
}) => {
  const yamlString = useMemo(() => {
    const kvPairs = displayMetadata.reduce(
      (accum, item) => {
        accum[item.key] = item.value;
        return accum;
      },
      {} as Record<string, string>,
    );
    return yaml.stringify(kvPairs);
  }, [displayMetadata]);

  return (
    <StyledRawCodeMirror
      value={yamlString}
      options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
      theme={['config-editor']}
    />
  );
};
