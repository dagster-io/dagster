import * as React from "react";
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
    const spark = metadata.find(m => m.key === "spark");
    if (!spark) return <span />;

    return (
      <div>
        {/* TODO: add this */}
        {spark.value}
      </div >
    );
  }
}
