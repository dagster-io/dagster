import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Colors } from "@blueprintjs/core";
import {
  ConfigEditorHelpContext,
  isHelpContextEqual
} from "../configeditor/ConfigEditor";
import { ConfigTypeSchema, TypeData } from "../ConfigTypeSchema";

interface ConfigEditorHelpProps {
  context: ConfigEditorHelpContext | null;
  allInnerTypes: TypeData[];
}

export const ConfigEditorHelp: React.FunctionComponent<ConfigEditorHelpProps> = React.memo(
  ({ context, allInnerTypes }) => {
    if (!context) {
      return <span />;
    }
    return (
      <Container>
        <ConfigScrollWrap>
          <ConfigTypeSchema
            type={context.type}
            typesInScope={allInnerTypes}
            theme="dark"
            maxDepth={2}
          />
        </ConfigScrollWrap>
        <AutocompletionsNote>
          Ctrl+Space to show auto-completions inline.
        </AutocompletionsNote>
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

const AutocompletionsNote = styled.div`
  font-size: 0.75rem;
  text-align: center;
  padding: 4px;
  border-top: 1px solid ${Colors.DARK_GRAY5};
  background: rgba(0, 0, 0, 0.07);
  color: rgba(255, 255, 255, 0.7);
`;

const ConfigScrollWrap = styled.div`
  padding: 8px;
  max-height: calc(100vh - 230px);
  overflow-y: auto;
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
  z-index: 3;
`;
