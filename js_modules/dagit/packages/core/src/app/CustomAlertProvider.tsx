import {Button, Dialog, DialogBody, DialogFooter, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {copyValue} from './DomUtils';

const CURRENT_ALERT_CHANGED = 'alert-changed';

interface ICustomAlert {
  body: React.ReactNode | string;
  title: string;
  copySelector?: string;
}

let CurrentAlert: ICustomAlert | null = null;

const setCustomAlert = (alert: ICustomAlert | null) => {
  CurrentAlert = alert;
  document.dispatchEvent(new CustomEvent(CURRENT_ALERT_CHANGED));
};

export const showCustomAlert = (opts: Partial<ICustomAlert>) => {
  setCustomAlert(Object.assign({body: '', title: 'Error'}, opts));
};

const REMOVAL_DELAY = 500;

export const CustomAlertProvider = () => {
  const [mounted, setMounted] = React.useState(false);
  const [alert, setAlert] = React.useState(() => CurrentAlert);
  const body = React.useRef<HTMLDivElement>(null);

  const copySelector = alert?.copySelector;

  React.useEffect(() => {
    const setter = () => setAlert(CurrentAlert);
    document.addEventListener(CURRENT_ALERT_CHANGED, setter);
    return () => document.removeEventListener(CURRENT_ALERT_CHANGED, setter);
  }, []);

  // When an alert is set, allow the Dialog to be mounted. When it is cleared,
  // remove the Dialog from the tree so that its root node doesn't linger in the DOM
  // and cause subsequent z-index bugs.
  React.useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (!!alert) {
      setMounted(true);
    } else {
      timer = setTimeout(() => setMounted(false), REMOVAL_DELAY);
    }
    return () => timer && clearTimeout(timer);
  }, [alert]);

  const onCopy = React.useCallback(
    (e: React.MouseEvent) => {
      const copyElement = copySelector ? body.current!.querySelector(copySelector) : body.current;
      const copyText =
        copyElement instanceof HTMLElement ? copyElement.innerText : copyElement?.textContent;
      copyValue(e, copyText || '');
    },
    [copySelector],
  );

  if (!mounted) {
    return null;
  }

  return (
    <Dialog
      title={alert?.title}
      icon={alert ? 'info' : undefined}
      onClose={() => setCustomAlert(null)}
      style={{width: 'auto', maxWidth: '80vw'}}
      isOpen={!!alert}
    >
      {alert ? (
        <DialogBody>
          <Body ref={body}>{alert.body}</Body>
        </DialogBody>
      ) : null}
      <DialogFooter>
        <Button autoFocus={false} onClick={onCopy}>
          Copy
        </Button>
        <Button intent="primary" autoFocus={true} onClick={() => setCustomAlert(null)}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const Body = styled.div`
  white-space: pre-line;
  font-family: ${FontFamily.monospace};
  font-size: 16px;
`;
