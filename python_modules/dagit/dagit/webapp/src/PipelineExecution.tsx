import * as React from "react";
import gql from "graphql-tag";
import * as yaml from "yaml";
import styled from "styled-components";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ApolloClient } from "apollo-boost";
import { ApolloConsumer } from "react-apollo";

import PipelineRun from "./PipelineRun";
import { ExecutionTabs } from "./ExecutionTabs";
import {
  applyConfigToSession,
  IExecutionSessionRun,
  IStorageData
} from "./LocalStorage";
import { PipelineExecutionFragment } from "./types/PipelineExecutionFragment";
import ConfigCodeEditorContainer from "./configeditor/ConfigCodeEditorContainer";
import Config from "./Config";
import {
  GetExecutionPlan,
  GetExecutionPlanVariables
} from "./types/GetExecutionPlan";
import {
  StartExecution,
  StartExecutionVariables
} from "./types/StartExecution";

interface IPipelineExecutionProps {
  pipeline: PipelineExecutionFragment;
  data: IStorageData;
  onSave: (data: IStorageData) => void;
}

export default class PipelineExecution extends React.Component<
  IPipelineExecutionProps
> {
  static fragments = {
    PipelineExecutionFragment: gql`
      fragment PipelineExecutionFragment on Pipeline {
        name
        environmentType {
          name
        }
        contexts {
          config {
            ...ConfigFragment
          }
        }
      }
      ${Config.fragments.ConfigFragment}
    `
  };

  public render() {
    const { pipeline, data, onSave } = this.props;
    const session = data.sessions[data.current];

    return (
      <>
        <ExecutionTabs data={data} onSave={onSave} />
        <Container>
          <Split>
            <ConfigCodeEditorContainer
              pipelineName={pipeline.name}
              environmentTypeName={pipeline.environmentType.name}
              configCode={session.config}
              onConfigChange={config =>
                onSave(applyConfigToSession(data, config))
              }
            />
          </Split>
          <Split>
            {session.lastRun ? (
              <PipelineRun run={session.lastRun} />
            ) : (
              <PipelineRun.Empty />
            )}
          </Split>
          <ApolloConsumer>
            {client => (
              <IconWrapper
                role="button"
                onClick={async () => {
                  let config = {};
                  try {
                    config = yaml.parse(session.config);
                  } catch (err) {
                    alert(`Fix the errors in your config YAML and try again.`);
                    return;
                  }
                  const executionParams = {
                    pipelineName: pipeline.name,
                    config: config
                  };
                  session.lastRun = await startRun(client, executionParams);
                  onSave(data);
                }}
              >
                <Icon icon={IconNames.PLAY} iconSize={40} />
              </IconWrapper>
            )}
          </ApolloConsumer>
        </Container>
      </>
    );
  }
}

const Container = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
  width: 100%;
`;

const IconWrapper = styled.div`
  flex: 0 1 0;
  width: 60px;
  height: 60px;
  border-radius: 30px;
  background-color: ${Colors.GRAY5};
  position: absolute;
  left: calc(50% - 30px);
  top: 120px;
  justify-content: center;
  align-items: center;
  display: flex;
  padding-left: 6px;
  cursor: pointer;

  &:hover {
    background-color: ${Colors.GRAY4};
  }

  &:active {
    background-color: ${Colors.GRAY3};
  }
`;

const Split = styled.div`
  flex: 1 1;
  flex-direction: column;
  display: flex;
`;

const GET_EXECUTION_PLAN = gql`
  query GetExecutionPlan($executionParams: PipelineExecutionParams!) {
    executionPlan(executionParams: $executionParams) {
      __typename
      ... on ExecutionPlan {
        steps {
          name
          solid {
            name
          }
          tag
        }
      }
    }
  }
`;

const START_PIPELINE_EXECUTION_MUTATION = gql`
  mutation StartExecution($executionParams: PipelineExecutionParams!) {
    startPipelineExecution(executionParams: $executionParams) {
      __typename

      ... on StartPipelineExecutionSuccess {
        run {
          runId
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineConfigValidationInvalid {
        errors {
          message
        }
      }
    }
  }
`;

async function startRun(
  client: ApolloClient<any>,
  executionParams: { config: object; pipelineName: string }
): Promise<IExecutionSessionRun> {
  // const {
  //   data: { executionPlan }
  // } = await client.query<GetExecutionPlan, GetExecutionPlanVariables>({
  //   query: GET_EXECUTION_PLAN,
  //   variables: { executionParams },
  //   fetchPolicy: "no-cache"
  // });

  // const result = await client.mutate<StartExecution, StartExecutionVariables>({
  //   mutation: START_PIPELINE_EXECUTION_MUTATION,
  //   variables: { executionParams },
  //   fetchPolicy: "no-cache"
  // });
  // if (
  //   result.data &&
  //   "startPipelineExecution" in result.data &&
  //   result.data.__typename === "StartPipelineExecutionSuccess" &&
  //   executionPlan.__typename === "ExecutionPlan"
  // ) {
  //   return {
  //     executionPlan,
  //     executionParams,
  //     runId: result.data.run.runId
  //   };
  // }

  return {
    executionParams: executionParams,
    executionPlan: {
      steps: [
        {
          name: "load_num_csv.transform",
          solid: {
            name: "load_num_csv"
          },
          tag: "TRANSFORM"
        },
        {
          name: "serialize.load_num_csv.result",
          solid: {
            name: "load_num_csv"
          },
          tag: "SERIALIZE"
        },
        {
          name: "sum_solid.transform",
          solid: {
            name: "sum_solid"
          },
          tag: "TRANSFORM"
        },
        {
          name: "serialize.sum_solid.result",
          solid: {
            name: "sum_solid"
          },
          tag: "SERIALIZE"
        },
        {
          name: "sum_sq_solid.transform",
          solid: {
            name: "sum_sq_solid"
          },
          tag: "TRANSFORM"
        },
        {
          name: "serialize.sum_sq_solid.result",
          solid: {
            name: "sum_sq_solid"
          },
          tag: "SERIALIZE"
        }
      ]
    },
    runId: "2fbbdb24-ae1e-43e7-8b32-c1ce3da0b419"
  };

  // todo handle errors - I assume this whole fn will be replaced soon

  throw new Error();
}
