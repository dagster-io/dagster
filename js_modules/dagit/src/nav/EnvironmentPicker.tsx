import React from "react";
import { Colors } from "@blueprintjs/core";
import { ProcessReloadButton } from "./ProcessReloadButton";

export const EnvironmentPicker: React.FunctionComponent<{}> = () => (
  <div
    style={{
      borderBottom: `1px solid ${Colors.DARK_GRAY4}`,
      padding: `10px 10px`,
      display: "flex",
      alignItems: "center"
    }}
  >
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 10.5, color: Colors.GRAY1 }}>ENVIRONMENT</div>
      Repository
    </div>
    <ProcessReloadButton />
  </div>
);
