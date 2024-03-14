import {Button, Dialog, DialogBody, DialogFooter, Icon} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';

import {HIDDEN_METADATA_ENTRY_LABELS} from '../metadata/MetadataEntry';
import {IPluginSidebarProps} from '../plugins';

export const SidebarComponent = (props: IPluginSidebarProps) => {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onOpen = () => setOpen(true);
    document.addEventListener('show-kind-info', onOpen);
    return () => document.removeEventListener('show-kind-info', onOpen);
  }, []);

  const metadata = props.definition.metadata
    .filter((m) => m.key !== 'kind' || !HIDDEN_METADATA_ENTRY_LABELS.has(m.key))
    .sort((a, b) => a.key.localeCompare(b.key));

  if (metadata.length === 0) {
    return <span />;
  }

  return (
    <div>
      <Button icon={<Icon name="content_copy" />} onClick={() => setOpen(true)}>
        View metadata
      </Button>
      <Dialog
        title={`Metadata: ${props.definition.name}`}
        isOpen={open}
        onClose={() => setOpen(false)}
      >
        <DialogBody>
          <div
            style={{
              maxHeight: 400,
              overflow: 'scroll',
            }}
          >
            <table className="bp4-html-table bp4-html-table-striped" style={{width: '100%'}}>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {metadata.map(({key, value}) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>
                      <code style={{whiteSpace: 'pre-wrap'}}>{value}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button onClick={() => setOpen(false)}>Close</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
};
