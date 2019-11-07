import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import {
  ConfigEditorHelpContext,
  isHelpContextEqual
} from "../configeditor/ConfigEditor";
import ConfigTypeSchema from "../ConfigTypeSchema";

interface ConfigEditorHelpProps {
  context: ConfigEditorHelpContext | null;
}

export const ConfigEditorHelp: React.FunctionComponent<ConfigEditorHelpProps> = React.memo(
  ({ context }) => {
    if (!context) {
      return <span />;
    }
    return (
      <Container>
        <ConfigTypeSchema type={context.type} theme="dark" maxDepth={2} />
      </Container>
    );
  },
  (prev, next) => isHelpContextEqual(prev.context, next.context)
);

export const ConfigEditorHelpConfigTypeFragment = gql`
  fragment ConfigEditorHelpConfigTypeFragment on ConfigType {
    ...ConfigTypeSchemaFragment
  }
  ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
`;

const Container = styled.div`
  width: 300px;
  top: 50px;
  right: 10px;
  color: white;
  border-top: 1px solid ${Colors.DARK_GRAY5};
  background-color: rgba(30, 40, 45, 0.7);
  position: absolute;
  align-items: center;
  padding: 8px;
  z-index: 3;
  max-height: calc(100vh - 210px);
  overflow-y: auto;
`;
