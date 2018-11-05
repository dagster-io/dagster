import * as React from "react";
import { Button, Classes, Dialog } from "@blueprintjs/core";
import { IPluginInterface, IPluginSidebarProps } from ".";

// TODO: Replace REACT_APP_GRAPHQL_URI with "DAGIT_SERVER_URI" without path
const NOTEBOOK_RENDERER_URI = process.env.REACT_APP_GRAPHQL_URI
  ? process.env.REACT_APP_GRAPHQL_URI.replace("/graphql", "/notebook")
  : "/notebook";

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

    const notebookPath = metadata.find(m => m.key === "notebook_path");
    if (!notebookPath || !notebookPath.value) return <span />;

    return (
      <div>
        <Button icon="duplicate" onClick={this.onClick}>
          View Notebook
        </Button>
        <Dialog
          icon="info-sign"
          onClose={() =>
            this.setState({
              open: false
            })
          }
          style={{ width: "80vw", maxWidth: 900, height: 615 }}
          title={notebookPath.value.split("/").pop()}
          usePortal={true}
          isOpen={this.state.open}
        >
          <div className={Classes.DIALOG_BODY} style={{ margin: 0 }}>
            <iframe
              src={`${NOTEBOOK_RENDERER_URI}${notebookPath.value}`}
              style={{ border: 0, background: "white" }}
              seamless={true}
              width="100%"
              height={500}
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
