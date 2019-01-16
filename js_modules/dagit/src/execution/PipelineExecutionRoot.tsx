import * as React from "react";
import gql from "graphql-tag";
import PipelineExecutionContainer from "./PipelineExecutionContainer";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { StorageProvider } from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";
import Loading from "../Loading";

interface IPipelineExecutionRootProps {
  pipeline: string;
}

interface IPipelineExecutionRootState {
  solidSubset: string[];
}

export default class PipelineExecutionRoot extends React.Component<
  IPipelineExecutionRootProps,
  IPipelineExecutionRootState
> {
  state = {
    solidSubset: []
  };

  render() {
    return (
      <ApolloConsumer>
        {client => (
          <StorageProvider namespace={this.props.pipeline}>
            {({ data, onSave }) => (
              <Query
                query={PIPELINE_EXECUTION_ROOT_QUERY}
                fetchPolicy="cache-and-network"
                partialRefetch={true}
                variables={{
                  name: this.props.pipeline,
                  solidSubset: this.state.solidSubset
                }}
              >
                {(
                  queryResult: QueryResult<PipelineExecutionRootQuery, any>
                ) => (
                  <Loading queryResult={queryResult}>
                    {result => (
                      <PipelineExecutionContainer
                        data={data}
                        onSave={onSave}
                        client={client}
                        pipeline={result.pipeline}
                        solidSubset={this.state.solidSubset}
                        onChangeSolidSubset={solidSubset =>
                          this.setState({ solidSubset })
                        }
                      />
                    )}
                  </Loading>
                )}
              </Query>
            )}
          </StorageProvider>
        )}
      </ApolloConsumer>
    );
  }
}

export const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query PipelineExecutionRootQuery($name: String!, $solidSubset: [String!]) {
    pipeline(name: $name, solidSubset: $solidSubset) {
      name
      ...PipelineExecutionContainerFragment
    }
  }

  ${PipelineExecutionContainer.fragments.PipelineExecutionContainerFragment}
`;
