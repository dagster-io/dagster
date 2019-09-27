import * as React from "react";
import { useQuery, useMutation, useApolloClient } from "react-apollo";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, Icon, Tooltip, Intent } from "@blueprintjs/core";
import { WebsocketStatusContext } from "./WebsocketStatus";
import { ProcessStatusQuery } from "./types/ProcessStatusQuery";
import { SharedToaster } from "./Util";

export default () => {
  const apollo = useApolloClient();
  const socketState = React.useContext(WebsocketStatusContext);
  const [reload] = useMutation(RELOAD_DAGIT_MUTATION);
  const [reloadStatus, setReloadStatus] = React.useState<
    "none" | "closing" | "waiting"
  >("none");

  const { data } = useQuery<ProcessStatusQuery>(PROCESS_STATUS_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  React.useEffect(() => {
    if (socketState === WebSocket.CLOSED && reloadStatus === "closing") {
      setReloadStatus("waiting");
    }
    if (socketState === WebSocket.OPEN && reloadStatus === "waiting") {
      setReloadStatus("none");

      // clears and re-fetches all the queries bound to the UI
      apollo.resetStore();

      // let the user know that something happened, since the refresh above is invisible
      // unless the user changed something shown in the current view.
      SharedToaster.show({
        message: "Repository Metadata Reloaded",
        timeout: 3000,
        icon: "refresh",
        intent: Intent.SUCCESS
      });
    }
  }, [socketState, reloadStatus, apollo]);

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
            disabled={reloadStatus !== "none"}
            onClick={() => {
              setReloadStatus("closing");
              reload();
            }}
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
