import * as React from "react";
import { useQuery, useMutation } from "react-apollo";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, Icon, Tooltip } from "@blueprintjs/core";
import { WebsocketStatusContext } from "./WebsocketStatus";
import { ProcessStatusQuery } from "./types/ProcessStatusQuery";

export default () => {
  const socketState = React.useContext(WebsocketStatusContext);
  const [reload] = useMutation(RELOAD_DAGIT_MUTATION);
  const { data } = useQuery<ProcessStatusQuery>(PROCESS_STATUS_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  if (!data) {
    return <span />;
  }

  return (
    <Label>
      {data.version}
      {data.reloadSupported && (
        <Tooltip
          hoverOpenDelay={500}
          content={
            <div style={{ maxWidth: 300 }}>
              Re-launch the web process and reload the UI to reflect the latest
              metadata, including DAG structure, solid names, type names, etc.
              <br />
              <br />
              Executing a pipeline run always uses the latest code on disk.
            </div>
          }
        >
          <Button
            small={true}
            text="Reload"
            style={{ marginLeft: 8 }}
            icon={<Icon icon="refresh" iconSize={12} />}
            disabled={socketState !== WebSocket.OPEN}
            onClick={() => reload()}
          />
        </Tooltip>
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
