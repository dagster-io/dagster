import * as React from "react";
import { Query, QueryResult } from "react-apollo";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { VersionQuery } from "./types/VersionQuery";

export default () => (
  <Query query={VERSION_QUERY}>
    {(queryResult: QueryResult<VersionQuery, { pipelineName: string }>) => (
      <Label>{queryResult.data && queryResult.data.version}</Label>
    )}
  </Query>
);

export const VERSION_QUERY = gql`
  query VersionQuery {
    version
  }
`;

const Label = styled.span`
  color: ${Colors.DARK_GRAY5};
  font-size: 0.8rem;
`;
