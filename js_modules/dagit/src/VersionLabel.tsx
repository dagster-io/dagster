import * as React from "react";
import { useQuery } from "react-apollo";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { VersionQuery } from "./types/VersionQuery";

export default () => {
  const result = useQuery<VersionQuery>(VERSION_QUERY, {
    fetchPolicy: "cache-and-network"
  });
  return <Label>{result.data && result.data.version}</Label>;
};

export const VERSION_QUERY = gql`
  query VersionQuery {
    version
  }
`;

const Label = styled.span`
  color: ${Colors.DARK_GRAY5};
  font-size: 0.8rem;
`;
