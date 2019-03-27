import * as React from "react";
import gql from "graphql-tag";
import { match } from "react-router";
import PipelineExecutionContainer from "./PipelineExecutionContainer";
import { QueryResult, Query } from "react-apollo";
import { StorageProvider } from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";

interface IPipelineExecutionRootProps {
  match: match<{ pipelineName: string }>;
}

export default class PipelineExecutionRoot extends React.Component<
  IPipelineExecutionRootProps
> {
  render() {
    const { pipelineName } = this.props.match.params;

    return (
      <StorageProvider namespace={pipelineName} key={pipelineName}>
        {({ data, onSave }) => {
          const vars = {
            name: pipelineName,
            solidSubset: data.sessions[data.current].solidSubset
          };
          return (
            <Query
              // never serve cached Pipeline given new vars by forcing teardown of the Query.
              // Apollo's behaviors are sort of whacky, even with no-cache. Should just use
              // window.fetch...
              key={JSON.stringify(vars)}
              query={PIPELINE_EXECUTION_ROOT_QUERY}
              fetchPolicy="cache-and-network"
              partialRefetch={true}
              variables={vars}
            >
              {(result: QueryResult<PipelineExecutionRootQuery, any>) => (
                <PipelineExecutionContainer
                  data={data}
                  onSave={onSave}
                  pipeline={(result.data && result.data.pipeline) || "loading"}
                  currentSession={data.sessions[data.current]}
                />
              )}
            </Query>
          );
        }}
      </StorageProvider>
    );
  }
}

export const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query PipelineExecutionRootQuery($name: String!, $solidSubset: [String!]) {
    pipeline(params: { name: $name, solidSubset: $solidSubset }) {
      name
      ...PipelineExecutionContainerFragment
    }
  }

  ${PipelineExecutionContainer.fragments.PipelineExecutionContainerFragment}
`;
