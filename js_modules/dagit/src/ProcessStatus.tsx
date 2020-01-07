import * as React from "react";
import { useQuery, useMutation, useApolloClient } from "react-apollo";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Colors, Button, Icon, Tooltip, Intent } from "@blueprintjs/core";
import { WebsocketStatusContext } from "./WebsocketStatus";
import { ProcessStatusQuery } from "./types/ProcessStatusQuery";
import { ShortcutHandler } from "./ShortcutHandler";
import { SharedToaster } from "./DomUtils";

export const ProcessStatus: React.FunctionComponent = () => {
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

  const onClick = () => {
    setReloadStatus("closing");
    reload();
  };
  return (
    <Label>
      {data.reloadSupported && (
        <ShortcutHandler
          onShortcut={onClick}
          shortcutLabel={`⌥R`}
          shortcutFilter={e => e.keyCode === 82 && e.altKey}
        >
          <Tooltip
            className="bp3-dark"
            hoverOpenDelay={500}
            content={
              <div style={{ maxWidth: 300 }}>
                Re-launch the web process and reload the UI to reflect the
                latest metadata, including DAG structure, solid names, type
                names, etc.
                <br />
                <br />
                Executing a pipeline run always uses the latest code on disk.
              </div>
            }
          >
            <Button
              icon={<Icon icon="refresh" iconSize={12} />}
              disabled={reloadStatus !== "none"}
              onClick={onClick}
            />
          </Tooltip>
        </ShortcutHandler>
      )}
      <div style={{ height: 14 }} />
      {data.instance && data.instance.info ? (
        <Tooltip
          hoverOpenDelay={500}
          content={
            <div style={{ whiteSpace: "pre-wrap" }}>{data.instance.info}</div>
          }
        >
          {data.version}
        </Tooltip>
      ) : (
        data.version
      )}
    </Label>
  );
};

export const PROCESS_STATUS_QUERY = gql`
  query ProcessStatusQuery {
    version
    reloadSupported
    instance {
      info
    }
  }
`;

const RELOAD_DAGIT_MUTATION = gql`
  mutation ReloadDagitMutation {
    reloadDagit
  }
`;

const Label = styled.span`
  color: ${Colors.LIGHT_GRAY1};
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  flex-direction: column;
`;
