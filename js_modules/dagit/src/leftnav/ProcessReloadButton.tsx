import * as React from "react";
import { useQuery, useMutation, useApolloClient } from "react-apollo";
import gql from "graphql-tag";
import { Button, Icon, Tooltip, Intent } from "@blueprintjs/core";
import { WebsocketStatusContext } from "./WebsocketStatus";
import { ReloadEnabledQuery } from "./types/ReloadEnabledQuery";
import { ShortcutHandler } from "../ShortcutHandler";
import { SharedToaster } from "../DomUtils";

export const ProcessReloadButton: React.FunctionComponent = () => {
  const apollo = useApolloClient();
  const socketState = React.useContext(WebsocketStatusContext);
  const [reload] = useMutation(RELOAD_DAGIT_MUTATION);
  const [reloadStatus, setReloadStatus] = React.useState<
    "none" | "closing" | "waiting"
  >("none");

  const { data } = useQuery<ReloadEnabledQuery>(RELOAD_ENABLED_QUERY, {
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
    <div>
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
    </div>
  );
};

export const RELOAD_ENABLED_QUERY = gql`
  query ReloadEnabledQuery {
    reloadSupported
  }
`;

const RELOAD_DAGIT_MUTATION = gql`
  mutation ReloadDagitMutation {
    reloadDagit
  }
`;
