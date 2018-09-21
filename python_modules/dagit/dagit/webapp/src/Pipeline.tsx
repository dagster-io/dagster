import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Switch, Route, match } from "react-router";
import { Link } from "react-router-dom";
import { Card, H3, H5, Text, Code, UL, H6 } from "@blueprintjs/core";
import SpacedCard from "./SpacedCard";
import Config from "./Config";
import Solid from "./Solid";
import PipelineGraph from "./graph/PipelineGraph";
import ConfigEditor from "./configeditor/ConfigEditor";
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
        contexts {
          name
          description
          config {
            ...ConfigFragment
          }
        }
        ...PipelineGraphFragment
        ...ConfigEditorFragment
      }

      ${Solid.fragments.SolidFragment}
      ${PipelineGraph.fragments.PipelineGraphFragment}
      ${SolidListItem.fragments.SolidListItemFragment}
      ${Config.fragments.ConfigFragment}
      ${ConfigEditor.fragments.ConfigEditorFragment}
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
            path="/:pipeline/config-editor"
            render={() => (
              <>
                <Breadcrumb>
                  <Link to={`/${this.props.pipeline.name}`}>
                    <BreadcrumbText>{this.props.pipeline.name}</BreadcrumbText>
                  </Link>
                </Breadcrumb>
                <Breadcrumb current={true}>
                  <BreadcrumbText>Config Editor</BreadcrumbText>
                </Breadcrumb>
              </>
            )}
          />
          <Route
            path="/:pipeline/:solid"
            render={({ match }) => (
              <>
                <Breadcrumb>
                  <Link to={`/${this.props.pipeline.name}`}>
                    <BreadcrumbText>{this.props.pipeline.name}</BreadcrumbText>
                  </Link>
                </Breadcrumb>
                <Breadcrumb current={true}>
                  <BreadcrumbText>{match.params.solid}</BreadcrumbText>
                </Breadcrumb>
              </>
            )}
          />
          <Route
            path="/:pipeline"
            render={() => (
              <>
                <Breadcrumb current={true}>
                  <BreadcrumbText>{this.props.pipeline.name}</BreadcrumbText>
                </Breadcrumb>
              </>
            )}
          />
        </Switch>
      </Breadcrumbs>
    );
  }

  renderContext() {
    return this.props.pipeline.contexts.map((context, i: number) => (
      <SpacedCard key={i}>
        <H5>
          <Code>{context.name}</Code>
        </H5>
        <DescriptionWrapper>
          <Description description={context.description} />
        </DescriptionWrapper>
        <Config config={context.config} />
      </SpacedCard>
    ));
  }

  renderSolids() {
    return this.props.pipeline.solids.map((solid, i: number) => (
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

  renderEditor = () => {
    return <ConfigEditor pipeline={this.props.pipeline} />;
  };

  renderSolidList = () => {
    return (
      <>
        <Section key="context">
          <H3>Context</H3>
          <ContextCards>{this.renderContext()}</ContextCards>
        </Section>
        <Section key="solids">
          <H3>Solids</H3>
          {this.renderSolids()}
        </Section>
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
        <Switch>
          <Route path="/:pipeline/config-editor" render={this.renderEditor} />
          <Route path="/:pipeline/:solid?" render={this.renderBody} />
        </Switch>
      </PipelineCard>
    );
  }
}

const BreadcrumbText = styled.h2`
  font-family: "Source Code Pro", monospace;
  font-weight: 500;
`;

const Section = styled.div`
  margin-bottom: 30px;
`;

const PipelineGraphWrapper = styled(Section)`
  height: 500px;
  width: 100%;
  display: flex;
`;

const PipelineCard = styled(Card)`
  flex: 1 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
