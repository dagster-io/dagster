import {Button, DagitReadOnlyCodeMirror, DialogFooter, Dialog, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {IPluginSidebarProps} from '../plugins';

export const SidebarComponent: React.FC<IPluginSidebarProps> = (props) => {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const onClose = () => setOpen(true);
    document.addEventListener('show-kind-info', onClose);
    return () => document.removeEventListener('show-kind-info', onClose);
  }, []);

  const metadata = props.definition.metadata;
  const sql = metadata.find((m) => m.key === 'sql');
  if (!sql) {
    return <span />;
  }

  return (
    <div>
      <Button icon={<Icon name="content_copy" />} onClick={() => setOpen(true)}>
        View SQL
      </Button>
      <Dialog
        icon="info"
        onClose={() => setOpen(false)}
        style={{width: '80vw', maxWidth: 900}}
        title={`SQL: ${props.definition.name}`}
        isOpen={open}
      >
        <DagitReadOnlyCodeMirror options={{lineNumbers: true, mode: 'sql'}} value={sql.value} />
        <DialogFooter topBorder>
          <Button intent="primary" onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
};
