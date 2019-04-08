import * as React from "react";
import { Button, Classes, Dialog } from "@blueprintjs/core";
import { IPluginSidebarProps } from ".";

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
    const spark = metadata.find(m => m.key === "kind" && m.value === "spark");
    if (!spark) {
      return <span />;
    }

    const mainClass = metadata.find(m => m.key === "main_class");

    if (!mainClass) {
      return <span />;
    }

    const displayString = "Main class: " + mainClass.value;

    return (
      <Dialog
        onClose={() =>
          this.setState({
            open: false
          })
        }
        isOpen={this.state.open}
      >
        <div className={Classes.DIALOG_BODY}>{displayString}</div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={() => this.setState({ open: false })}>
              Close
            </Button>
          </div>
        </div>
      </Dialog>
    );
  }
}
