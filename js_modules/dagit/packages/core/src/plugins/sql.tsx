import {
  ButtonWIP,
  DialogBody,
  DialogFooter,
  DialogWIP,
  HighlightedCodeBlock,
  IconWIP,
} from '@dagster-io/ui';
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
      <ButtonWIP icon={<IconWIP name="content_copy" />} onClick={() => setOpen(true)}>
        View SQL
      </ButtonWIP>
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
