import * as React from "react";
import { Query, QueryResult } from "react-apollo";
import gql from "graphql-tag";
import { VersionQuery } from "./types/VersionQuery";

export default () => (
  <Query query={VERSION_QUERY}>
    {(queryResult: QueryResult<VersionQuery, { pipelineName: string }>) => (
      <span>{queryResult.data && queryResult.data.version}</span>
    )}
  </Query>
);

export const VERSION_QUERY = gql`
  query VersionQuery {
    version
  }
`;
