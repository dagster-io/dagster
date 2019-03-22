import * as React from "react";
import { Button, Dialog, Classes, Colors } from "@blueprintjs/core";
import styled from "styled-components";

const SHOW_ALERT_EVENT = "show-alert";

export const showCustomAlert = (opts: { message: string }) => {
  document.dispatchEvent(
    new CustomEvent(SHOW_ALERT_EVENT, {
      detail: opts.message
    })
  );
};

export default class CustomAlertProvider extends React.Component<
  {},
  { text: string | null }
> {
  state = {
    text: null
  };

  componentDidMount() {
    document.addEventListener(SHOW_ALERT_EVENT, (e: CustomEvent) => {
      this.setState({ text: e.detail });
    });
  }

  render() {
    return (
      <Dialog
        icon="info-sign"
        onClose={() => this.setState({ text: null })}
        style={{ width: "auto", maxWidth: "80vw" }}
        title={"Error"}
        usePortal={true}
        isOpen={!!this.state.text}
      >
        <Body>{this.state.text}</Body>

        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button
              intent="primary"
              autoFocus={true}
              onClick={() => this.setState({ text: null })}
            >
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
  max-height: 500px;
  background: ${Colors.WHITE};
  border-top: 1px solid ${Colors.LIGHT_GRAY3};
  padding: 20px;
  margin: 0;
  margin-bottom: 20px;
`;
