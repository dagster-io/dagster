import {Button, DialogBody, DialogFooter, Dialog, Icon, ExternalAnchorButton} from '@dagster-io/ui';
import * as React from 'react';

import {AppContext} from '../app/AppContext';

export const NotebookButton: React.FC<{
  path?: string;
  repoLocation: string;
  label?: string;
}> = ({path, repoLocation, label}) => {
  const {rootServerURI} = React.useContext(AppContext);
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const onOpen = () => setOpen(true);
    document.addEventListener('show-kind-info', onOpen);
    return () => document.removeEventListener('show-kind-info', onOpen);
  }, []);

  const value = path || '';
  const url = React.useMemo(() => {
    try {
      const url = new URL(value);
      return url.toString();
    } catch (e) {
      // Not a full valid URL
      return null;
    }
  }, [value]);

  if (!path) {
    return <span />;
  }

  const buttonLabel = label || 'View Notebook';

  if (url) {
    return (
      <ExternalAnchorButton href={url} icon={<Icon name="open_in_new" />}>
        {buttonLabel}
      </ExternalAnchorButton>
    );
  }
  return (
    <div>
      <Button icon={<Icon name="content_copy" />} onClick={() => setOpen(true)}>
        {buttonLabel}
      </Button>
      <Dialog
        icon="info"
        onClose={() => setOpen(false)}
        style={{width: '80vw', maxWidth: 900}}
        title={path.split('/').pop()}
        usePortal={true}
        isOpen={open}
      >
        <DialogBody>
          <iframe
            title={path}
            src={`${rootServerURI}/dagit/notebook?path=${encodeURIComponent(
              path,
            )}&repoLocName=${repoLocation}`}
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
};
