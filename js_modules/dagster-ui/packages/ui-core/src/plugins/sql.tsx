import * as React from 'react';

import {Button, Dialog, DialogFooter, Icon, StyledRawCodeMirror} from '@dagster-io/ui-components';

import {IPluginSidebarProps} from '../plugins';

export const SidebarComponent = (props: IPluginSidebarProps) => {
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
        <StyledRawCodeMirror
          options={{readOnly: true, lineNumbers: true, mode: 'sql'}}
          value={sql.value}
        />
        <DialogFooter topBorder>
          <Button intent="primary" onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
};
