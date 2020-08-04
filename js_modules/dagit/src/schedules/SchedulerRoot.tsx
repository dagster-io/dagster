import * as React from "react";
import { ScrollContainer, Header } from "../ListComponents";
import { SchedulerInfo, SCHEDULER_FRAGMENT } from "./SchedulerInfo";
import { useQuery } from "react-apollo";
import Loading from "../Loading";
import gql from "graphql-tag";
import { SchedulerRootQuery } from "./types/SchedulerRootQuery";

export const SchedulerRoot: React.FunctionComponent<{}> = () => {
  const queryResult = useQuery<SchedulerRootQuery>(SCHEDULER_ROOT_QUERY, {
    variables: {},
    fetchPolicy: "cache-and-network"
  });

  return (
    <ScrollContainer>
      <Header>Scheduler</Header>
      <Loading queryResult={queryResult} allowStaleData={true}>
        {result => {
          const { scheduler } = result;
          return <SchedulerInfo schedulerOrError={scheduler} />;
        }}
      </Loading>
    </ScrollContainer>
  );
};

export const SCHEDULER_ROOT_QUERY = gql`
  query SchedulerRootQuery {
    scheduler {
      ...SchedulerFragment
    }
  }

  ${SCHEDULER_FRAGMENT}
`;
