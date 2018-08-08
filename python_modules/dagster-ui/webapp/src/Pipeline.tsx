import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Route, match } from "react-router";
import { Link } from "react-router-dom";
import { Card, H2, H5, Text, Code, UL, Classes } from "@blueprintjs/core";
import SpacedCard from "./SpacedCard";
import Argumented from "./Argumented";
import Solid from "./Solid";
import PipelineGraph from "./graph/PipelineGraph";
import { Breadcrumbs, Breadcrumb } from "./Breadcrumbs";
import { PipelineFragment } from "./types/PipelineFragment";

interface IPipelineProps {
  pipeline: PipelineFragment;
}

export default class Pipeline extends React.Component<IPipelineProps, {}> {
  static fragments = {
    PipelineFragment: gql`
      fragment PipelineFragment on Pipeline {
        name
        description
        solids {
          ...SolidFragment
        }
        context {
          ...PipelineContextFragment
        }
        ...PipelineGraphFragment
      }

      ${Solid.fragments.SolidFragment}
      ${Argumented.fragments.PipelineContextFragment}
      ${PipelineGraph.fragments.PipelineGraphFragment}
    `
  };

  handleClickSolid = (
    history: History,
    activeSolid: string | null,
    solidName: string
  ) => {
    if (solidName === activeSolid) {
      history.push(`/${this.props.pipeline.name}`);
    } else {
      history.push(`/${this.props.pipeline.name}/${solidName}`);
    }
  };

  renderContext() {
    return this.props.pipeline.context.map((context: any, i: number) => (
      <Argumented key={i} item={context} />
    ));
  }

  renderSolids() {
    return this.props.pipeline.solids.map((solid: any, i: number) => (
      <li key={i}>
        <Link to={`/${this.props.pipeline.name}/${solid.name}`}>
          <Code>{solid.name}</Code>
        </Link>{" "}
        - ({solid.output.type.name})<Text>{solid.description}</Text>
      </li>
    ));
  }

  renderSolidList = ({ history }: { history: History }) => {
    return (
      <>
        <PipelineGraphWrapper key="graph">
          <PipelineGraph
            pipeline={this.props.pipeline}
            onClickSolid={solidName =>
              this.handleClickSolid(history, null, solidName)
            }
          />
        </PipelineGraphWrapper>
        <SpacedCard elevation={1} key="solids">
          <H5>Solids</H5>
          <UL>{this.renderSolids()}</UL>
        </SpacedCard>
        <SpacedCard elevation={1} key="context">
          <H5>Context</H5>
          {this.renderContext()}
        </SpacedCard>
      </>
    );
  };

  renderSolid = ({
    history,
    match
  }: {
    history: History;
    match: match<{ pipeline: string; solid: string }>;
  }) => {
    const solidName = match.params.solid;
    const solid = this.props.pipeline.solids.find(
      ({ name }) => name === solidName
    );
    if (solid) {
      return (
        <>
          <PipelineGraphWrapper key="graph">
            <PipelineGraph
              pipeline={this.props.pipeline}
              selectedSolid={solidName}
              onClickSolid={newSolidName =>
                this.handleClickSolid(history, solidName, newSolidName)
              }
            />
          </PipelineGraphWrapper>
          <Solid solid={solid} />
        </>
      );
    } else {
      return null;
    }
  };

  public render() {
    return (
      <PipelineCard>
        <SpacedWrapper>
          <Breadcrumbs>
            <Route
              path="/:pipeline/:solid"
              render={({ match }) => (
                <>
                  <Breadcrumb>
                    <H2>
                      <Link to={`/${this.props.pipeline.name}`}>
                        <Code>{this.props.pipeline.name}</Code>
                      </Link>
                    </H2>
                  </Breadcrumb>
                  <Breadcrumb current={true}>
                    <H2>
                      <Code>{match.params.solid}</Code>
                    </H2>
                  </Breadcrumb>
                </>
              )}
            />
            <Route
              exact={true}
              path="/:pipeline"
              render={() => (
                <>
                  <Breadcrumb current={true}>
                    <H2>
                      <Code>{this.props.pipeline.name}</Code>
                    </H2>
                  </Breadcrumb>
                </>
              )}
            />
          </Breadcrumbs>
        </SpacedWrapper>
        <SpacedWrapper>
          <Text>{this.props.pipeline.description}</Text>
        </SpacedWrapper>
        <Route path="/:pipeline/:solid" render={this.renderSolid} />
        <Route exact={true} path="/:pipeline" render={this.renderSolidList} />
      </PipelineCard>
    );
  }
}

const PipelineGraphWrapper = styled(Card)`
  height: 500px;
  width: 100%;
  display: flex;
  margin: 10px 0 0 0;
`;

const PipelineCard = styled(Card)`
  flex: 1 1;
  overflow: hidden;
`;

const SpacedWrapper = styled.div`
  margin-top: 10px;
`;
