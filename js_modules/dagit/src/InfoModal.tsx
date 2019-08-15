import * as React from "react";
import { Classes, Dialog } from "@blueprintjs/core";

interface IInfoModalProps {
  children: React.ReactElement;
  title?: string;
  onRequestClose: () => void;
}

export default ({ children, title, onRequestClose }: IInfoModalProps) => {
  return (
    <Dialog
      icon="info-sign"
      onClose={onRequestClose}
      style={{ width: "80vw", maxWidth: 1400 }}
      title={title || "Info"}
      usePortal={true}
      isOpen={true}
    >
      <div className={Classes.DIALOG_BODY}>{children}</div>
    </Dialog>
  );
};
