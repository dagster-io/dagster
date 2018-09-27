import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Switch, Route, match } from "react-router";
import { Colors } from "@blueprintjs/core";
import ConfigCodeEditor from "./ConfigCodeEditor";
import ConfigExplorer from "./ConfigExplorer";
import TypeExplorerContainer from "./TypeExplorerContainer";
import { ConfigEditorFragment } from "./types/ConfigEditorFragment";

interface IConfigEditorProps {
  pipeline: ConfigEditorFragment;
  match: match<any>;
  history: History;
}

export default class ConfigEditor extends React.Component<
  IConfigEditorProps,
  {}
> {
  static fragments = {
    ConfigEditorFragment: gql`
      fragment ConfigEditorFragment on Pipeline {
        name
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
        <Border />
        <TypeExplorerWrapper>
          <Route
            path={`${this.props.match.url}/:typeName`}
            render={({ match }: { match: match<{ typeName: string }> }) => {
              return (
                <TypeExplorerContainer
                  pipelineName={this.props.pipeline.name}
                  typeName={match.params.typeName}
                />
              );
            }}
          />
        </TypeExplorerWrapper>
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

const TypeExplorerWrapper = styled.div`
  flex: 1 1;
`;
