import {Button, Dialog, Classes} from '@blueprintjs/core';
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
  const repoLocName = props.repoAddress?.location;

  if (!notebookPath) {
    return <span />;
  }

  return (
    <div>
      <Button icon="duplicate" onClick={() => setOpen(true)}>
        View Notebook
      </Button>
      <Dialog
        icon="info-sign"
        onClose={() => setOpen(false)}
        style={{width: '80vw', maxWidth: 900, height: 615}}
        title={notebookPath.value.split('/').pop()}
        usePortal={true}
        isOpen={open}
      >
        <div className={Classes.DIALOG_BODY} style={{margin: 0}}>
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
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={() => setOpen(false)}>Close</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};
