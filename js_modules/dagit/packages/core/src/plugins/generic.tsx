import {Button, DialogBody, DialogFooter, Dialog, Icon} from '@dagster-io/ui';
import startCase from 'lodash/startCase';
import * as React from 'react';

import {IPluginSidebarProps} from '../plugins';

export const SidebarComponent: React.FC<IPluginSidebarProps> = (props) => {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const onOpen = () => setOpen(true);
    document.addEventListener('show-kind-info', onOpen);
    return () => document.removeEventListener('show-kind-info', onOpen);
  }, []);

  const metadata = props.definition.metadata
    .filter((m) => m.key !== 'kind')
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
            <table className="bp3-html-table bp3-html-table-striped" style={{width: '100%'}}>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {metadata.map(({key, value}) => (
                  <tr key={key}>
                    <td>{startCase(key)}</td>
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
