import * as React from "react";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { Spinner } from "@blueprintjs/core";
import { InstanceDetailsQuery } from "./types/InstanceDetailsQuery";
import { ScrollContainer, Header } from "./ListComponents";

export const InstanceDetailsRoot: React.FunctionComponent = () => {
  const { data } = useQuery<InstanceDetailsQuery>(INSTANCE_DETAILS_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  return data ? (
    <ScrollContainer>
      <Header>{`Dagster ${data.version}`}</Header>
      <div style={{ whiteSpace: "pre-wrap" }}>{data?.instance.info}</div>
    </ScrollContainer>
  ) : (
    <Spinner size={35} />
  );
};

export const INSTANCE_DETAILS_QUERY = gql`
  query InstanceDetailsQuery {
    version
    instance {
      info
    }
  }
`;
