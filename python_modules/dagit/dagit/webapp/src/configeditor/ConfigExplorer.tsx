import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { H4, H5, Colors, Code } from "@blueprintjs/core";
import Config from "../Config";
import Description from "../Description";
import { ConfigExplorerFragment } from "./types/ConfigExplorerFragment";

interface IConfigExplorerProps {
  pipeline: ConfigExplorerFragment;
}

export default class ConfigExplorer extends React.Component<
  IConfigExplorerProps,
  {}
> {
  static fragments = {
    ConfigExplorerFragment: gql`
      fragment ConfigExplorerFragment on Pipeline {
        ...ConfigPipelineTypesFragment

        contexts {
          name
          description
          config {
            ...ConfigFragment
          }
        }
        solids {
          definition {
            name
            description
            configDefinition {
              ...ConfigFragment
            }
          }
        }
      }

      ${Config.fragments.ConfigFragment}
      ${Config.fragments.ConfigPipelineTypesFragment}
    `
  };

  renderContexts() {
    return this.props.pipeline.contexts.map((context, i: number) => (
      <div key={i}>
        <H5>
          <Code>{context.name}</Code>
        </H5>
        <DescriptionWrapper>
          <Description description={context.description} />
        </DescriptionWrapper>
        {context.config && (
          <Config config={context.config} pipeline={this.props.pipeline} />
        )}
      </div>
    ));
  }

  renderSolids() {
    return this.props.pipeline.solids.map((solid, i: number) => (
      <div key={i}>
        <H5>
          <Code>{solid.definition.name}</Code>
        </H5>
        <DescriptionWrapper>
          <Description description={solid.definition.description} />
        </DescriptionWrapper>
        {solid.definition.configDefinition && (
          <Config
            config={solid.definition.configDefinition}
            pipeline={this.props.pipeline}
          />
        )}
      </div>
    ));
  }

  render() {
    return (
      <ConfigExplorerWrapper>
        <H4>Contexts</H4>
        {this.renderContexts()}
        <H4>Solid configs</H4>
        {this.renderSolids()}
      </ConfigExplorerWrapper>
    );
  }
}
const ConfigExplorerWrapper = styled.div`
  max-width: 500px;
`;

const SpacedWrapper = styled.div`
  margin-bottom: 10px;
`;

const DescriptionWrapper = styled(SpacedWrapper)`
  max-width: 500px;
`;
