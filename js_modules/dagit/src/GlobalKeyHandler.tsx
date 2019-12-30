import * as React from "react";

export class GlobalKeyHandler extends React.Component<{
  onGlobalKeydown: (event: KeyboardEvent) => void;
}> {
  componentDidMount() {
    window.addEventListener("keydown", this.onGlobalKeydown);
  }

  componentWillUnmount() {
    window.removeEventListener("keydown", this.onGlobalKeydown);
  }

  onGlobalKeydown = (event: KeyboardEvent) => {
    const { target } = event;

    if (
      (target && (target as HTMLElement).nodeName === "INPUT") ||
      (target as HTMLElement).nodeName === "TEXTAREA"
    ) {
      return;
    }
    this.props.onGlobalKeydown(event);
  };

  render() {
    return this.props.children;
  }
}
