import * as React from "react";
import { Button, Classes, Dialog } from "@blueprintjs/core";
import { IPluginSidebarProps } from ".";
import { highlightBlock } from "highlight.js";

import "highlight.js/styles/xcode.css";

class HighlightedSQL extends React.Component<{ sql: string; style: {} }> {
  _el = React.createRef<HTMLPreElement>();

  componentDidMount() {
    if (this._el.current) highlightBlock(this._el.current);
  }

  render() {
    const { sql, ...rest } = this.props;
    return (
      <pre ref={this._el} {...rest}>
        {sql}
      </pre>
    );
  }
}

export class SidebarComponent extends React.Component<IPluginSidebarProps> {
  state = {
    open: false
  };

  componentDidMount() {
    document.addEventListener("show-kind-info", this.onClick);
  }

  componentWillUnmount() {
    document.removeEventListener("show-kind-info", this.onClick);
  }

  onClick = () => {
    this.setState({
      open: true
    });
  };

  render() {
    const metadata = this.props.solid.definition.metadata;
    if (!metadata) return <span />;

    const sql = metadata.find(m => m.key === "sql");
    if (!sql || !sql.value) return <span />;

    return (
      <div>
        <Button icon="duplicate" onClick={this.onClick}>
          View SQL
        </Button>
        <Dialog
          icon="info-sign"
          onClose={() =>
            this.setState({
              open: false
            })
          }
          style={{ width: "80vw", maxWidth: 900, height: 615 }}
          title={`SQL: ${this.props.solid.name}`}
          usePortal={true}
          isOpen={this.state.open}
        >
          <div className={Classes.DIALOG_BODY} style={{ margin: 0 }}>
            <HighlightedSQL
              sql={sql.value}
              style={{
                height: 510,
                margin: 0,
                overflow: "scroll",
                fontSize: "0.9em"
              }}
            />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={() => this.setState({ open: false })}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    );
  }
}
