import {Button} from '@blueprintjs/core';
import * as React from 'react';

import {IPluginSidebarProps} from '../plugins';
import {ButtonWIP} from '../ui/Button';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {HighlightedCodeBlock} from '../ui/HighlightedCodeBlock';

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
      <Button icon="duplicate" onClick={() => setOpen(true)}>
        View SQL
      </Button>
      <DialogWIP
        icon="info"
        onClose={() => setOpen(false)}
        style={{width: '80vw', maxWidth: 900, height: 615}}
        title={`SQL: ${props.definition.name}`}
        isOpen={open}
      >
        <DialogBody>
          <HighlightedCodeBlock
            language="sql"
            value={sql.value}
            style={{
              height: 510,
              padding: 10,
              overflow: 'scroll',
              fontSize: '0.9em',
            }}
          />
        </DialogBody>
        <DialogFooter>
          <ButtonWIP onClick={() => setOpen(false)}>Close</ButtonWIP>
        </DialogFooter>
      </DialogWIP>
    </div>
  );
};
