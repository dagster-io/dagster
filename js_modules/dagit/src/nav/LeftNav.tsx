import * as React from "react";
import { Link } from "react-router-dom";
import { useRouteMatch, useHistory } from "react-router";
import styled from "styled-components/macro";
import { Colors, Icon } from "@blueprintjs/core";

import { InstanceDetailsLink } from "./InstanceDetailsLink";
import { WebsocketStatus } from "../WebsocketStatus";
import { ShortcutHandler } from "../ShortcutHandler";
import { EnvironmentPicker } from "./EnvironmentPicker";
import { EnvironmentContentList } from "./EnvironmentContentList";
import navBarImage from "../images/nav-logo-icon.png";
import navTitleImage from "../images/nav-title.png";
import { DagsterRepoOption } from "../DagsterRepositoryContext";

const KEYCODE_FOR_1 = 49;

const INSTANCE_TABS = [
  {
    to: `/runs`,
    tab: `runs`,
    icon: <Icon icon="history" iconSize={18} />,
    label: "Runs"
  },
  {
    to: `/assets`,
    tab: `assets`,
    icon: <Icon icon="panel-table" iconSize={18} />,
    label: "Assets"
  }
];

const REPO_SCOPE_TABS = [
  {
    to: `/schedules`,
    tab: `schedules`,
    icon: <Icon icon="calendar" iconSize={18} />,
    label: "Schedules"
  }
];

interface LeftNavProps {
  options: DagsterRepoOption[];
  repo: DagsterRepoOption | null;
  setRepo: (repo: DagsterRepoOption) => void;
}

export const LeftNav: React.FunctionComponent<LeftNavProps> = ({
  options,
  repo,
  setRepo
}) => {
  const history = useHistory();
  const match = useRouteMatch<
    | { selector: string; tab: string; rootTab: undefined }
    | { selector: undefined; tab: undefined; rootTab: string }
  >(["/pipeline/:selector/:tab?", "/solid/:selector", "/:rootTab?"]);

  return (
    <LeftNavContainer>
      <div style={{ flexShrink: 0 }}>
        <LogoContainer>
          <img
            alt="logo"
            src={navBarImage}
            style={{ height: 40 }}
            onClick={() => history.push("/")}
          />
          <LogoMetaContainer>
            <img src={navTitleImage} style={{ height: 10 }} alt="title" />
            <InstanceDetailsLink />
          </LogoMetaContainer>
          <LogoWebsocketStatus />
        </LogoContainer>
        {INSTANCE_TABS.map((t, i) => (
          <ShortcutHandler
            key={t.tab}
            onShortcut={() => history.push(t.to)}
            shortcutLabel={`⌥${i + 1}`}
            shortcutFilter={e => e.keyCode === KEYCODE_FOR_1 + i && e.altKey}
          >
            <Tab
              to={t.to}
              className={match?.params.rootTab === t.tab ? "selected" : ""}
            >
              {t.icon}
              <TabLabel>{t.label}</TabLabel>
            </Tab>
          </ShortcutHandler>
        ))}
      </div>
      <div style={{ height: 40 }} />
      <div
        className="bp3-dark"
        style={{
          background: `rgba(0,0,0,0.3)`,
          color: Colors.WHITE,
          flex: 1
        }}
      >
        <EnvironmentPicker options={options} repo={repo} setRepo={setRepo} />
        {repo &&
          REPO_SCOPE_TABS.map(t => (
            <Tab
              to={t.to}
              key={t.tab}
              className={match?.params.tab === t.tab ? "selected" : ""}
            >
              {t.icon}
              <TabLabel>{t.label}</TabLabel>
            </Tab>
          ))}
        {repo && <EnvironmentContentList {...match?.params} repo={repo} />}
        <div style={{ flex: 1 }} />
      </div>
    </LeftNavContainer>
  );
};

const LogoWebsocketStatus = styled(WebsocketStatus)`
  position: absolute;
  top: 28px;
  left: 42px;
`;

const LeftNavContainer = styled.div`
  width: 235px;
  height: 100%;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: center;
  background: ${Colors.DARK_GRAY2};
  border-right: 1px solid ${Colors.DARK_GRAY5};
  padding-top: 14px;
`;

const Tab = styled(Link)`
  color: ${Colors.LIGHT_GRAY1} !important;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  display: flex;
  padding: 8px 12px;
  margin: 0px 0;
  align-items: center;
  outline: 0;
  &:hover {
    color: ${Colors.WHITE} !important;
    text-decoration: none;
  }
  &:focus {
    outline: 0;
  }
  &.selected {
    color: ${Colors.WHITE} !important;
    border-left: 4px solid ${Colors.COBALT3};
    font-weight: 600;
  }
`;

const TabLabel = styled.div`
  font-size: 13px;
  margin-left: 6px;
  text-decoration: none;
  white-space: nowrap;
  text-decoration: none;
`;

const LogoContainer = styled.div`
  width: 100%;
  padding: 0 10px;
  margin-bottom: 10px;
  position: relative;
  cursor: pointer;
  &:hover {
    img {
      filter: brightness(110%);
    }
  }
`;

const LogoMetaContainer = styled.div`
  position: absolute;
  left: 56px;
  top: -3px;
  height: 42px;
  padding-left: 4px;
  right: 0;
  z-index: 1;
  border-bottom: 1px solid ${Colors.DARK_GRAY4};
`;
