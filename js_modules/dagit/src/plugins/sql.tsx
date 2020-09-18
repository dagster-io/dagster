import {Button, Classes, Dialog} from '@blueprintjs/core';
import * as React from 'react';

import {HighlightedCodeBlock} from '../HighlightedCodeBlock';

import {IPluginSidebarProps} from '.';

export class SidebarComponent extends React.Component<IPluginSidebarProps> {
  state = {
    open: false,
  };

  componentDidMount() {
    document.addEventListener('show-kind-info', this.onClick);
  }

  componentWillUnmount() {
    document.removeEventListener('show-kind-info', this.onClick);
  }

  onClick = () => {
    this.setState({
      open: true,
    });
  };

  render() {
    const metadata = this.props.definition.metadata;
    const sql = metadata.find((m) => m.key === 'sql');
    if (!sql) return <span />;

    return (
      <div>
        <Button icon="duplicate" onClick={this.onClick}>
          View SQL
        </Button>
        <Dialog
          icon="info-sign"
          onClose={() =>
            this.setState({
              open: false,
            })
          }
          style={{width: '80vw', maxWidth: 900, height: 615}}
          title={`SQL: ${this.props.definition.name}`}
          usePortal={true}
          isOpen={this.state.open}
        >
          <div className={Classes.DIALOG_BODY} style={{margin: 0}}>
            <HighlightedCodeBlock
              languages={['sql']}
              value={sql.value}
              style={{
                height: 510,
                margin: 0,
                overflow: 'scroll',
                fontSize: '0.9em',
              }}
            />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={() => this.setState({open: false})}>Close</Button>
            </div>
          </div>
        </Dialog>
      </div>
    );
  }
}
