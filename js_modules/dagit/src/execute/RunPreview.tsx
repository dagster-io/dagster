import * as React from "react";
import * as YAML from "yaml";
import gql from "graphql-tag";
import styled from "styled-components";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import ApolloClient from "apollo-client";
import { ApolloConsumer } from "react-apollo";
import ExecutionPlan from "../ExecutionPlan";
import {
  ExecutionPlanPreviewQuery,
  ExecutionPlanPreviewQueryVariables
} from "./types/ExecutionPlanPreviewQuery";

export const EXECUTION_PLAN_PREVIEW_QUERY = gql`
  query ExecutionPlanPreviewQuery(
    $pipeline: ExecutionSelector!
    $config: PipelineConfig!
  ) {
    executionPlan(pipeline: $pipeline, config: $config) {
      __typename
      ... on ExecutionPlan {
        ...ExecutionPlanFragment
      }
      ... on PipelineNotFoundError {
        message
      }
    }
  }

  ${ExecutionPlan.fragments.ExecutionPlanFragment}
`;

interface IRunPreviewProps {
  pipelineName: string;
  solidSubset: string[] | null;
  configCode: string;
}

interface IRunPreviewState {
  data: ExecutionPlanPreviewQuery | null;
}

export class RunPreviewConnected extends React.Component<
  IRunPreviewProps & { client: ApolloClient<any> },
  IRunPreviewState
> {
  _fetchTimer: NodeJS.Timeout;
  _mounted = false;
  state: IRunPreviewState = {
    data: null
  };

  componentDidMount() {
    this._mounted = true;
    this.fetchPlan();
  }

  componentDidUpdate(prevProps: IRunPreviewProps) {
    if (
      prevProps.configCode !== this.props.configCode ||
      prevProps.pipelineName !== this.props.pipelineName ||
      prevProps.solidSubset !== this.props.solidSubset
    ) {
      this.fetchPlanSoon();
    }
  }

  componentWillUnmount() {
    clearTimeout(this._fetchTimer);
    this._mounted = false;
  }

  fetchPlanSoon() {
    clearTimeout(this._fetchTimer);
    this._fetchTimer = setTimeout(() => this.fetchPlan(), 250);
  }

  async fetchPlan() {
    let config = null;
    try {
      config = YAML.parse(this.props.configCode);
    } catch (err) {
      // no-op
    }

    if (!config) {
      this.setState({ data: null });
      return;
    }

    const { data } = await this.props.client.query<
      ExecutionPlanPreviewQuery,
      ExecutionPlanPreviewQueryVariables
    >({
      query: EXECUTION_PLAN_PREVIEW_QUERY,
      variables: {
        config,
        pipeline: {
          name: this.props.pipelineName,
          solidSubset: this.props.solidSubset
        }
      },
      fetchPolicy: "no-cache"
    });

    if (!this._mounted) return;
    this.setState({ data });
  }

  render() {
    const { data } = this.state;

    return data && data.executionPlan.__typename === "ExecutionPlan" ? (
      <ExecutionPlan executionPlan={data.executionPlan} />
    ) : (
      <NonIdealState
        icon={IconNames.SEND_TO_GRAPH}
        title="No Execution Plan"
        description={"Provide valid configuration to see an execution plan."}
      />
    );
  }
}

export const RunPreview: React.FC<IRunPreviewProps> = props => (
  <PreviewWrapper>
    <ApolloConsumer>
      {client => <RunPreviewConnected client={client} {...props} />}
    </ApolloConsumer>
  </PreviewWrapper>
);

const PreviewWrapper = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1 1;
  min-height: 0;
`;
