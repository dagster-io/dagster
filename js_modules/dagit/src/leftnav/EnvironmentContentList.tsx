import React from "react";
import {
  Colors,
  InputGroup,
  ButtonGroup,
  Button,
  Icon
} from "@blueprintjs/core";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { Link, Route } from "react-router-dom";
import styled from "styled-components/macro";

import { PipelineNamesContext } from "../PipelineNamesContext";
import { ContentListSolidsQuery } from "./types/ContentListSolidsQuery";

const iincludes = (haystack: string, needle: string) =>
  haystack.toLowerCase().includes(needle.toLowerCase());

export const EnvironmentContentList: React.FunctionComponent<{}> = () => {
  const [type, setType] = React.useState<"pipelines" | "solids">("pipelines");
  const pipelineNames = React.useContext(PipelineNamesContext);
  const [q, setQ] = React.useState<string>("");

  const solids = useQuery<ContentListSolidsQuery>(CONTENT_LIST_SOLIDS_QUERY, {
    fetchPolicy: "cache-first"
  });

  React.useEffect(() => {
    if (type === "solids") {
      solids.refetch();
    }
  }, [type, solids]);

  return (
    <Route
      path="/:tab?/:pipelineSelector?"
      render={({ match: { params } }) => {
        const tab = params.tab === "playground" ? "playground" : "pipeline";
        const currentItemName = params.pipelineSelector?.split(":")[0];

        return (
          <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
            <Header>
              <InputGroup
                type="text"
                value={q}
                small
                placeholder={`Search ${type}...`}
                onChange={(e: React.ChangeEvent<any>) => setQ(e.target.value)}
                style={{
                  border: `1px solid ${Colors.DARK_GRAY5}`,
                  background: Colors.DARK_GRAY4
                }}
              />
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
            {type === "pipelines" ? (
              <Items>
                {pipelineNames
                  .filter(p => !q || iincludes(p, q))
                  .map(p => (
                    <React.Fragment key={p}>
                      <Item
                        to={`/${tab}/${p}/`}
                        className={p === currentItemName ? "selected" : ""}
                      >
                        {p}
                      </Item>
                      {p === currentItemName && (
                        <div>
                          <Subitem
                            to={`/pipeline/${p}/`}
                            className={tab === "pipeline" ? "selected" : ""}
                          >
                            <Icon
                              iconSize={14}
                              icon="diagram-tree"
                              style={{ marginRight: 8 }}
                            />
                            Definition
                          </Subitem>
                          <Subitem
                            to={`/playground/${p}/`}
                            className={tab === "playground" ? "selected" : ""}
                          >
                            <Icon
                              iconSize={14}
                              icon="manually-entered-data"
                              style={{ marginRight: 8 }}
                            />
                            Playground
                          </Subitem>
                        </div>
                      )}
                    </React.Fragment>
                  ))}
              </Items>
            ) : (
              <Items>
                {solids.data?.usedSolids
                  .filter(
                    s =>
                      !q ||
                      iincludes(s.definition.name, q) ||
                      s.invocations.some(i => iincludes(i.pipeline.name, q))
                  )
                  .map(({ definition }) => (
                    <Item
                      key={definition.name}
                      to={`/solid/${definition.name}`}
                      className={
                        definition.name === currentItemName ? "selected" : ""
                      }
                    >
                      {definition.name}
                    </Item>
                  ))}
              </Items>
            )}
          </div>
        );
      }}
    />
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
  max-height: calc(100vh - 300px);
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
  display: block;
  color: ${Colors.LIGHT_GRAY3} !important;
  &:hover {
    text-decoration: none;
    color: ${Colors.WHITE} !important;
  }
  &:active {
    outline: 0;
    border-left: 4px solid ${Colors.DARK_GRAY4};
  }
  &.selected {
    outline: 0;
    border-left: 4px solid ${Colors.COBALT3};
    border-bottom: 1px solid ${Colors.DARK_GRAY2};
    background: ${Colors.BLACK};
    font-weight: 600;
    color: ${Colors.WHITE} !important;
  }
`;

const Subitem = styled(Item)`
  padding: 4px 12px;
  padding-left: 14px;
  border-left: 4px solid ${Colors.COBALT3};
  background: ${Colors.BLACK};
  color: ${Colors.LIGHT_GRAY3} !important;

  &.selected,
  &:active {
    outline: 0;
    border-left: 4px solid ${Colors.COBALT3};
    background: ${Colors.COBALT1};
    font-weight: 300;
    color: ${Colors.WHITE} !important;
  }
  &:last-child {
    margin-bottom: 10px;
  }
`;

export const CONTENT_LIST_SOLIDS_QUERY = gql`
  query ContentListSolidsQuery {
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
`;
