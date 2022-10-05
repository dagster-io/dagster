import {Button, DialogBody, DialogFooter, Dialog, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {IPluginSidebarProps} from '../plugins';

export const SidebarComponent: React.FC<IPluginSidebarProps> = (props) => {
  const {rootServerURI} = React.useContext(AppContext);
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const onOpen = () => setOpen(true);
    document.addEventListener('show-kind-info', onOpen);
    return () => document.removeEventListener('show-kind-info', onOpen);
  }, []);

  const metadata = props.definition.metadata;
  const notebookPath = metadata.find((m) => m.key === 'notebook_path');
  const notebookKind = metadata.find((m) => m.key === 'kind');
  const repoLocName = props.repoAddress?.location;

  if (!notebookPath) {
    return <span />;
  }

  if (notebookKind && notebookKind.value === 'noteable') {
    return (
      <div>
        <Button
          icon={<Icon name="content_copy" />}
          onClick={() => window.open(notebookPath.value, '_blank', 'noopener,noreferrer')}
        >
          View Notebook
        </Button>
      </div>
    );
  } else {
    return (
      <div>
        <Button icon={<Icon name="content_copy" />} onClick={() => setOpen(true)}>
          View Notebook
        </Button>
        <Dialog
          icon="info"
          onClose={() => setOpen(false)}
          style={{width: '80vw', maxWidth: 900}}
          title={notebookPath.value.split('/').pop()}
          usePortal={true}
          isOpen={open}
        >
          <DialogBody>
            <iframe
              title={notebookPath.value}
              src={`${rootServerURI}/dagit/notebook?path=${encodeURIComponent(
                notebookPath.value,
              )}&repoLocName=${repoLocName}`}
              sandbox=""
              style={{border: 0, background: 'white'}}
              seamless={true}
              width="100%"
              height={500}
            />
          </DialogBody>
          <DialogFooter>
            <Button onClick={() => setOpen(false)}>Close</Button>
          </DialogFooter>
        </Dialog>
      </div>
    );
  }
};
