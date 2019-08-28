import * as React from "react";
import { Button, Dialog, Classes, Colors } from "@blueprintjs/core";
import styled from "styled-components";
import { copyValue } from "./Util";

const SHOW_ALERT_EVENT = "show-alert";

interface ICustomAlert {
  body: React.ReactNode | string;
  title: string;
}

export const showCustomAlert = (opts: Partial<ICustomAlert>) => {
  document.dispatchEvent(
    new CustomEvent(SHOW_ALERT_EVENT, {
      detail: JSON.stringify(
        Object.assign({ message: "", title: "Error", pre: false }, opts)
      )
    })
  );
};

export default class CustomAlertProvider extends React.Component<
  {},
  Partial<ICustomAlert>
> {
  state: Partial<ICustomAlert> = {};

  bodyRef = React.createRef<HTMLDivElement>();

  componentDidMount() {
    document.addEventListener(SHOW_ALERT_EVENT, (e: CustomEvent) => {
      this.setState(JSON.parse(e.detail));
    });
  }

  render() {
    const { title, body } = this.state;

    return (
      <Dialog
        icon={title ? "info-sign" : undefined}
        usePortal={true}
        onClose={() => this.setState({ body: undefined })}
        style={{ width: "auto", maxWidth: "80vw" }}
        title={title}
        isOpen={!!body}
      >
        <Body ref={this.bodyRef}>{body}</Body>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button
              autoFocus={false}
              onClick={(e: React.MouseEvent<any, MouseEvent>) =>
                copyValue(e, this.bodyRef.current!.textContent || "")
              }
            >
              Copy
            </Button>
            <Button
              intent="primary"
              autoFocus={true}
              onClick={() => this.setState({ body: undefined })}
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
