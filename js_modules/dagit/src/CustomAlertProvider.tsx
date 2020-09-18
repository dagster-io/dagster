import {Button, Classes, Colors, Dialog} from '@blueprintjs/core';
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

export const setCustomAlert = (alert: ICustomAlert | null) => {
  CurrentAlert = alert;
  document.dispatchEvent(new CustomEvent(CURRENT_ALERT_CHANGED));
};

export const showCustomAlert = (opts: Partial<ICustomAlert>) => {
  setCustomAlert(Object.assign({body: '', title: 'Error'}, opts));
};

export default class CustomAlertProvider extends React.Component<{}, {alert: ICustomAlert | null}> {
  state = {alert: CurrentAlert};

  bodyRef = React.createRef<HTMLDivElement>();

  componentDidMount() {
    document.addEventListener(CURRENT_ALERT_CHANGED, () => this.setState({alert: CurrentAlert}));
  }

  render() {
    const alert = this.state.alert;

    return (
      <Dialog
        icon={alert ? 'info-sign' : undefined}
        usePortal={true}
        onClose={() => setCustomAlert(null)}
        style={{width: 'auto', maxWidth: '80vw'}}
        title={alert ? alert.title : ''}
        isOpen={!!alert}
      >
        <Body ref={this.bodyRef}>{alert ? alert.body : undefined}</Body>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button
              autoFocus={false}
              onClick={(e: React.MouseEvent<any, MouseEvent>) => {
                const copyElement = alert?.copySelector
                  ? this.bodyRef.current!.querySelector(alert.copySelector)
                  : this.bodyRef.current;
                copyValue(e, copyElement?.textContent || '');
              }}
            >
              Copy
            </Button>
            <Button intent="primary" autoFocus={true} onClick={() => setCustomAlert(null)}>
              OK
            </Button>
          </div>
        </div>
      </Dialog>
    );
  }
}

const Body = styled.div`
  white-space: pre-line;
  font-family: Consolas, Menlo, monospace;
  font-size: 13px;
  overflow: scroll;
  background: ${Colors.WHITE};
  border-top: 1px solid ${Colors.LIGHT_GRAY3};
  padding: 20px;
  margin: 0;
  margin-bottom: 20px;
`;
