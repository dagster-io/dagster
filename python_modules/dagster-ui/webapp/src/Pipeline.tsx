import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Switch, Route, match } from "react-router";
import { Link } from "react-router-dom";
import { Card, H2, H5, Text, Code, UL } from "@blueprintjs/core";
import SpacedCard from "./SpacedCard";
import Argumented from "./Argumented";
import Solid from "./Solid";
import PipelineGraph from "./graph/PipelineGraph";
import { Breadcrumbs, Breadcrumb } from "./Breadcrumbs";
import SolidListItem from "./SolidListItem";
import Description from "./Description";
import {
  PipelineFragment,
  PipelineFragment_solids
} from "./types/PipelineFragment";

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
          ...SolidListItemFragment
        }
        context {
          ...PipelineContextFragment
        }
        ...PipelineGraphFragment
      }

      ${Solid.fragments.SolidFragment}
      ${Argumented.fragments.PipelineContextFragment}
      ${PipelineGraph.fragments.PipelineGraphFragment}
      ${SolidListItem.fragments.SolidListItemFragment}
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

  renderBreadcrumbs() {
    return (
      <Breadcrumbs>
        <Switch>
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
        </Switch>
      </Breadcrumbs>
    );
  }

  renderContext() {
    return this.props.pipeline.context.map((context: any, i: number) => (
      <Argumented
        key={i}
        item={context}
        renderCard={props => <ContextCard horizontal={true} {...props} />}
      />
    ));
  }

  renderSolids() {
    return this.props.pipeline.solids.map((solid: any, i: number) => (
      <SolidListItem
        pipelineName={this.props.pipeline.name}
        solid={solid}
        key={i}
      />
    ));
  }

  renderBody = ({
    history,
    match
  }: {
    history: History;
    match: match<{ pipeline: string; solid?: string }>;
  }) => {
    const solidName = match.params.solid;
    let solid: PipelineFragment_solids | undefined;
    if (solidName) {
      solid = this.props.pipeline.solids.find(({ name }) => name === solidName);
    }
    let body;
    if (solid) {
      body = <Solid solid={solid} />;
    } else {
      body = this.renderSolidList();
    }
    return (
      <>
        <PipelineGraphWrapper key="graph">
          <PipelineGraph
            pipeline={this.props.pipeline}
            selectedSolid={solidName}
            onClickSolid={solidName =>
              this.handleClickSolid(
                history,
                solid ? solid.name : null,
                solidName
              )
            }
          />
        </PipelineGraphWrapper>
        {body}
      </>
    );
  };

  renderSolidList = () => {
    return (
      <>
        <SpacedCard elevation={1} key="context">
          <H5>Context</H5>
          <ContextCards>{this.renderContext()}</ContextCards>
        </SpacedCard>
        <SpacedCard elevation={1} key="solids">
          <H5>Solids</H5>
          <UL>{this.renderSolids()}</UL>
        </SpacedCard>
      </>
    );
  };

  public render() {
    return (
      <PipelineCard>
        <SpacedWrapper>{this.renderBreadcrumbs()}</SpacedWrapper>
        <DescriptionWrapper>
          <Description description={this.props.pipeline.description} />
        </DescriptionWrapper>
        <Route path="/:pipeline/:solid?" render={this.renderBody} />
      </PipelineCard>
    );
  }
}

const PipelineGraphWrapper = styled(Card)`
  height: 500px;
  width: 100%;
  display: flex;
  margin-bottom: 10px;
`;

const PipelineCard = styled(Card)`
  flex: 1 1;
  overflow: hidden;
`;

const SpacedWrapper = styled.div`
  margin-bottom: 10px;
`;

const ContextCards = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
`;

const ContextCard = styled(SpacedCard)`
  width: 400px;
  margin-bottom: 10px;
`;

const DescriptionWrapper = styled(SpacedWrapper)`
  max-width: 500px;
`;
