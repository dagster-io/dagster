import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { History } from "history";
import Loading from "./Loading";
import Pipelines from "./Pipelines";
import { PipelinesContainerQuery } from "./types/PipelinesContainerQuery";

interface IPipelinesContainerProps {
  pipelineName: string;
  history: History;
}

export default class PipelinesContainer extends React.Component<
  IPipelinesContainerProps,
  {}
> {
  render() {
    return (
      <Query query={PIPELINES_CONTAINER_QUERY}>
        {(queryResult: QueryResult<PipelinesContainerQuery, any>) => {
          return (
            <Loading queryResult={queryResult}>
              {data => {
                return (
                  <Pipelines
                    selectedPipeline={this.props.pipelineName}
                    pipelines={data.pipelines}
                    history={this.props.history}
                  />
                );
              }}
            </Loading>
          );
        }}
      </Query>
    );
  }
}

export const PIPELINES_CONTAINER_QUERY = gql`
  query PipelinesContainerQuery {
    pipelines {
      ...PipelinesFragment
    }
  }

  ${Pipelines.fragments.PipelinesFragment}
`;
