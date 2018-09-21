import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import ConfigCodeEditor from "./ConfigCodeEditor";
import ConfigExplorer from "./ConfigExplorer";
import { ConfigEditorFragment } from "./types/ConfigEditorFragment";

interface IConfigEditorProps {
  pipeline: ConfigEditorFragment;
}

export default class ConfigEditor extends React.Component<
  IConfigEditorProps,
  {}
> {
  static fragments = {
    ConfigEditorFragment: gql`
      fragment ConfigEditorFragment on Pipeline {
        ...ConfigExplorerFragment
      }

      ${ConfigExplorer.fragments.ConfigExplorerFragment}
    `
  };

  render() {
    return (
      <Split>
        <ConfigCodeEditorWrapper>
          <ConfigCodeEditor />
        </ConfigCodeEditorWrapper>
        <Border />
        <ConfigExplorerWrapper>
          <ConfigExplorer pipeline={this.props.pipeline} />
        </ConfigExplorerWrapper>
      </Split>
    );
  }
}

const Split = styled.div`
  display: flex;
  flex-direction: row;
  flex: 1 1;
  height: 100%;
`;

const Border = styled.div`
  flex: 0 0 1px
  background-color: ${Colors.GRAY5};
  margin: 0 20px;
`;

const ConfigCodeEditorWrapper = styled.div`
  flex: 0 0 auto;
  height: 100%;
`;

const ConfigExplorerWrapper = styled.div`
  flex: 1 1;
`;
