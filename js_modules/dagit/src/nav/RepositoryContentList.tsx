import React from "react";
import { Colors, InputGroup, ButtonGroup, Button, Icon } from "@blueprintjs/core";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { Link } from "react-router-dom";
import styled from "styled-components/macro";

import { tabForPipelinePathComponent } from "./PipelineNav";
import { ContentListSolidsQuery } from "./types/ContentListSolidsQuery";
import { DagsterRepoOption } from "../DagsterRepositoryContext";
import { ShortcutHandler } from "../ShortcutHandler";
import { useHistory } from "react-router";

const iincludes = (haystack: string, needle: string) =>
  haystack.toLowerCase().includes(needle.toLowerCase());

interface RepositoryContentListProps {
  selector?: string;
  tab?: string;
  repo: DagsterRepoOption;
}

export const RepositoryContentList: React.FunctionComponent<RepositoryContentListProps> = ({
  tab,
  repo,
  selector
}) => {
  const [type, setType] = React.useState<"pipelines" | "solids">("pipelines");
  const [focused, setFocused] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const pipelineTab = tabForPipelinePathComponent(tab);

  const history = useHistory();

  const [q, setQ] = React.useState<string>("");
  // Load solids, but only if the user clicks on the Solid option
  const solids = useQuery<ContentListSolidsQuery>(CONTENT_LIST_SOLIDS_QUERY, {
    fetchPolicy: "cache-first",
    variables: {
      repositorySelector: {
        repositoryLocationName: repo.repositoryLocation.name,
        repositoryName: repo.repository.name
      }
    }
  });
  React.useEffect(() => {
    if (type === "solids") {
      solids.refetch();
    }
  }, [type, solids]);
  const usedSolids =
    solids.data?.repositoryOrError?.__typename === "Repository"
      ? solids.data.repositoryOrError.usedSolids
      : [];

  const items =
    type === "pipelines"
      ? repo.repository.pipelines
          .map(pipeline => pipeline.name)
          .filter(p => !q || iincludes(p, q))
          .map(p => ({
            to: `/pipeline/${p}/${tab === "partitions" ? "overview" : pipelineTab.pathComponent}`,
            label: p
          }))
      : usedSolids
          .filter(
            s =>
              !q ||
              iincludes(s.definition.name, q) ||
              s.invocations.some(i => iincludes(i.pipeline.name, q))
          )
          .map(({ definition }) => ({
            to: `/solid/${definition.name}`,
            label: definition.name
          }));

  const onShiftFocus = (dir: 1 | -1) => {
    const idx = items.findIndex(p => p.label === focused);
    if (idx === -1 && items[0]) {
      setFocused(items[0].label);
    } else if (items[idx + dir]) {
      setFocused(items[idx + dir].label);
    }
  };

  const onConfirmFocused = () => {
    if (focused) {
      const item = items.find(p => p.label === focused);
      if (item) {
        history.push(item.to);
        return;
      }
    }
    if (items.length) {
      history.push(items[0].to);
      setFocused(items[0].label);
    }
  };

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        borderTop: `1px solid ${Colors.DARK_GRAY4}`
      }}
    >
      <Header>
        <ShortcutHandler
          onShortcut={() => inputRef.current?.focus()}
          shortcutFilter={e => e.altKey && e.keyCode === 80}
          shortcutLabel={`⌥P then Up / Down`}
        >
          <InputGroup
            type="text"
            inputRef={c => (inputRef.current = c)}
            value={q}
            small
            placeholder={`Search ${type}...`}
            onKeyDown={e => {
              if (e.key === "ArrowDown") {
                onShiftFocus(1);
              }
              if (e.key === "ArrowUp") {
                onShiftFocus(-1);
              }
              if (e.key === "Enter" || e.key === "Return") {
                onConfirmFocused();
              }
            }}
            onChange={(e: React.ChangeEvent<any>) => setQ(e.target.value)}
            style={{
              border: `1px solid ${Colors.DARK_GRAY5}`,
              background: Colors.DARK_GRAY4
            }}
          />
        </ShortcutHandler>
        <div style={{ width: 4 }} />
        <ButtonGroup>
          <Button
            small={true}
            active={type === "pipelines"}
            intent={type === "pipelines" ? "primary" : "none"}
            icon={<Icon icon="diagram-tree" iconSize={13} />}
            onClick={() => setType("pipelines")}
          />
          <Button
            small={true}
            active={type === "solids"}
            intent={type === "solids" ? "primary" : "none"}
            icon={<Icon icon="git-commit" iconSize={13} />}
            onClick={() => setType("solids")}
          />
        </ButtonGroup>
      </Header>
      <Items>
        {items.map(p => (
          <Item
            key={p.label}
            data-tooltip={p.label}
            data-tooltip-style={p.label === selector ? SelectedItemTooltipStyle : ItemTooltipStyle}
            className={`${p.label === selector ? "selected" : ""} ${
              p.label === focused ? "focused" : ""
            }`}
            to={p.to}
          >
            {p.label}
          </Item>
        ))}
      </Items>
    </div>
  );
};

const Header = styled.div`
  margin: 6px 10px;
  display: flex;
  & .bp3-input-group {
    flex: 1;
  }
`;

const Items = styled.div`
  flex: 1;
  overflow: auto;
  max-height: calc((100vh - 405px) / 2);
  &::-webkit-scrollbar {
    width: 11px;
  }

  scrollbar-width: thin;
  scrollbar-color: ${Colors.GRAY1} ${Colors.DARK_GRAY1};

  &::-webkit-scrollbar-track {
    background: ${Colors.DARK_GRAY1};
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${Colors.GRAY1};
    border-radius: 6px;
    border: 3px solid ${Colors.DARK_GRAY1};
  }
`;

const Item = styled(Link)`
  font-size: 13px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 8px 12px;
  padding-left: 8px;
  border-left: 4px solid transparent;
  border-bottom: 1px solid transparent;
  display: block;
  color: ${Colors.LIGHT_GRAY3} !important;
  &:hover {
    text-decoration: none;
    color: ${Colors.WHITE} !important;
  }
  &:focus {
    outline: 0;
  }
  &.focused {
    border-left: 4px solid ${Colors.GRAY3};
  }
  &.selected {
    border-left: 4px solid ${Colors.COBALT3};
    border-bottom: 1px solid ${Colors.DARK_GRAY2};
    background: ${Colors.BLACK};
    font-weight: 600;
    color: ${Colors.WHITE} !important;
  }
`;

const BaseTooltipStyle = {
  fontSize: 13,
  padding: 3,
  paddingRight: 7,
  left: 9,
  top: 5,
  color: Colors.WHITE,
  background: Colors.DARK_GRAY1,
  transform: "none",
  border: 0,
  borderRadius: 4
};

const ItemTooltipStyle = JSON.stringify({
  ...BaseTooltipStyle,
  color: Colors.WHITE,
  background: Colors.DARK_GRAY1
});

const SelectedItemTooltipStyle = JSON.stringify({
  ...BaseTooltipStyle,
  color: Colors.WHITE,
  background: Colors.BLACK,
  fontWeight: 600
});

export const CONTENT_LIST_SOLIDS_QUERY = gql`
  query ContentListSolidsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolids {
          __typename
          definition {
            name
          }
          invocations {
            __typename
            pipeline {
              name
            }
          }
        }
      }
    }
  }
`;
