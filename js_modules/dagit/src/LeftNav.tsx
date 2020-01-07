import * as React from "react";

import { Colors, Icon } from "@blueprintjs/core";

import { Link } from "react-router-dom";
import { Route } from "react-router";
import { ProcessStatus } from "./ProcessStatus";
import { WebsocketStatus } from "./WebsocketStatus";
import navBarImage from "./images/nav-logo-icon.png";
import styled from "styled-components/macro";
import { PipelineNamesContext } from "./PipelineNamesContext";
import { GlobalKeyHandler } from "./GlobalKeyHandler";

const LAST_PIPELINE = "last-pipeline";
const KEYCODE_FOR_1 = 49;

export const LeftNav = () => {
  const pipelineNames = React.useContext(PipelineNamesContext);

  return (
    <Route
      path="/:tab?/:pipelineSelector?"
      render={({ match: { params }, history }) => {
        const { tab } = params;

        // When you click the Pipeline tab, navigate to the last pipeline you've
        // viewed by storing a small amount of state in localStorage.
        if (tab === "pipeline") {
          localStorage.setItem(LAST_PIPELINE, params.pipelineSelector);
        }

        let pipelineSelector = localStorage.getItem(LAST_PIPELINE);
        if (!pipelineSelector) {
          pipelineSelector = `${pipelineNames[0]}:`;
        }
        if (
          pipelineNames &&
          !pipelineNames.includes(pipelineSelector.split(":")[0])
        ) {
          pipelineSelector = `${pipelineNames[0]}:`;
        }

        const TABS = [
          {
            to: `/pipeline/${pipelineSelector}/`,
            tab: `pipeline`,
            icon: <Icon icon="diagram-tree" iconSize={30} />,
            label: "Pipelines"
          },
          {
            to: `/solids`,
            tab: `solids`,
            icon: <Icon icon="git-commit" iconSize={30} />,
            label: "Solids"
          },
          {
            to: `/runs`,
            tab: `runs`,
            icon: <Icon icon="history" iconSize={30} />,
            label: "Runs"
          },
          {
            to: `/playground`,
            tab: `playground`,
            icon: <Icon icon="manually-entered-data" iconSize={30} />,
            label: "Playground"
          },
          {
            to: `/scheduler`,
            tab: `scheduler`,
            icon: <Icon icon="calendar" iconSize={30} />,
            label: "Schedule"
          }
        ];

        const onGlobalKeydown = (event: KeyboardEvent) => {
          if (
            event.altKey &&
            event.keyCode >= KEYCODE_FOR_1 &&
            event.keyCode < KEYCODE_FOR_1 + TABS.length
          ) {
            history.push(TABS[event.keyCode - KEYCODE_FOR_1].to);
          }
        };

        return (
          <GlobalKeyHandler onGlobalKeydown={onGlobalKeydown}>
            <Tabs>
              <LogoContainer onClick={() => history.push("/")}>
                <img src={navBarImage} style={{ height: 40 }} alt="logo" />
                <LogoWebsocketStatus />
              </LogoContainer>
              {TABS.map(t => (
                <Tab
                  to={t.to}
                  key={t.tab}
                  className={tab === t.tab ? "active" : ""}
                >
                  {t.icon}
                  <TabLabel>{t.label}</TabLabel>
                </Tab>
              ))}
              <div style={{ flex: 1 }} />
              <ProcessStatus />
            </Tabs>
          </GlobalKeyHandler>
        );
      }}
    />
  );
};

const LogoWebsocketStatus = styled(WebsocketStatus)`
  position: absolute;
  top: 28px;
  right: -3px;
`;

const Tabs = styled.div`
  width: 74px;
  height: 100%;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: center;
  background: ${Colors.DARK_GRAY2};
  border-right: 1px solid ${Colors.DARK_GRAY5};
  padding: 14px 0;
`;

const Tab = styled(Link)`
  color: ${Colors.LIGHT_GRAY1};
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4px 0;
  margin: 8px 0;
  align-items: center;
  outline: 0;
  &:hover {
    color: ${Colors.WHITE};
    text-decoration: none;
  }
  &.active {
    color: ${Colors.WHITE};
    border-left: 4px solid ${Colors.COBALT3};
  }
`;

const TabLabel = styled.div`
  font-size: 11px;
  margin-top: 6px;
  text-decoration: none;
  white-space: nowrap;
  text-decoration: none;
`;

const LogoContainer = styled.div`
  margin: auto;
  margin-bottom: 10px;
  position: relative;
`;
