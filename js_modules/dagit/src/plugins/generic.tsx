import {Button, Classes, Dialog} from '@blueprintjs/core';
import {startCase} from 'lodash';
import * as React from 'react';

import {IPluginSidebarProps} from 'src/plugins';

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
    const metadata = this.props.definition.metadata.sort((a, b) => a.key.localeCompare(b.key));

    if (metadata.length === 0) {
      return <span />;
    }

    return (
      <div>
        <Button icon="duplicate" onClick={this.onClick}>
          View Metadata
        </Button>
        <Dialog
          title={`Metadata: ${this.props.definition.name}`}
          isOpen={this.state.open}
          onClose={() =>
            this.setState({
              open: false,
            })
          }
        >
          <div
            className={Classes.DIALOG_BODY}
            style={{
              maxHeight: 400,
              overflow: 'scroll',
            }}
          >
            <table className="bp3-html-table bp3-html-table-striped" style={{width: '100%'}}>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {metadata.map(({key, value}) => (
                  <tr key={key}>
                    <td>{startCase(key)}</td>
                    <td>
                      <code style={{whiteSpace: 'pre-wrap'}}>{value}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
