import * as React from "react";
import { useQuery, useMutation, useApolloClient } from "react-apollo";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, Spinner, Icon } from "@blueprintjs/core";
import { WebsocketStatusContext } from "./WebsocketStatus";
import { ProcessStatusQuery } from "./types/ProcessStatusQuery";

export default () => {
  const apollo = useApolloClient();
  const socketState = React.useContext(WebsocketStatusContext);
  const [reload] = useMutation(RELOAD_DAGIT_MUTATION);
  const [reloading, setReloading] = React.useState<boolean>(false);
  const { data } = useQuery<ProcessStatusQuery>(PROCESS_STATUS_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  React.useEffect(() => {
    if (socketState === WebSocket.OPEN && reloading) {
      setReloading(false);
      apollo.resetStore();
    } else if (socketState !== WebSocket.OPEN && !reloading) {
      setReloading(true);
    }
  }, [socketState, reloading, apollo]);

  if (!data) {
    return <span />;
  }

  return (
    <Label>
      {data.version}
      {data.reloadSupported && (
        <Button
          small={true}
          text="Reload"
          style={{ marginLeft: 8 }}
          icon={
            reloading ? (
              <Spinner size={12} />
            ) : (
              <Icon icon="refresh" iconSize={12} />
            )
          }
          disabled={reloading || socketState !== WebSocket.OPEN}
          onClick={() => reload()}
        />
      )}
    </Label>
  );
};

export const PROCESS_STATUS_QUERY = gql`
  query ProcessStatusQuery {
    version
    reloadSupported
  }
`;

const RELOAD_DAGIT_MUTATION = gql`
  mutation ReloadDagitMutation {
    reloadDagit
  }
`;

const Label = styled.span`
  color: ${Colors.DARK_GRAY5};
  font-size: 0.8rem;
  display: flex;
  align-items: center;
`;
