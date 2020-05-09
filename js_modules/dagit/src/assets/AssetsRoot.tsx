import * as React from "react";
import styled from "styled-components";
import { Select } from "@blueprintjs/select";
import { NonIdealState, Colors } from "@blueprintjs/core";
import { Button, MenuItem } from "@blueprintjs/core";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { AssetsRootQuery_assetsOrError_AssetConnection_nodes } from "./types/AssetsRootQuery";
import Loading from "../Loading";
import { Link, RouteComponentProps } from "react-router-dom";
import { AssetRoot } from "./AssetRoot";
import {
  Header,
  Legend,
  LegendColumn,
  RowContainer,
  RowColumn
} from "../ListComponents";

type Asset = AssetsRootQuery_assetsOrError_AssetConnection_nodes;

export const AssetsRoot: React.FunctionComponent<RouteComponentProps<{
  assetSelector: string;
}>> = ({ match, history }) => {
  const assetName = decodeURIComponent(match.params.assetSelector);
  const queryResult = useQuery(ASSETS_ROOT_QUERY);

  const onSelect = (assetName: string) => {
    history.push(`/assets/${encodeURIComponent(assetName)}`);
  };

  return (
    <Loading queryResult={queryResult}>
      {({ assetsOrError }) => {
        if (assetsOrError.__typename === "AssetsNotSupportedError") {
          return (
            <Wrapper>
              <NonIdealState
                icon="panel-table"
                title="Assets"
                description={
                  <p>
                    An asset-aware event storage (e.g.{" "}
                    <code>PostgresEventLogStorage</code>) must be configured in
                    order to use any Asset-based features. You can configure
                    this on your instance through <code>dagster.yaml</code>. See
                    the{" "}
                    <a href="https://docs.dagster.io/docs/deploying/instance#event-log-storage">
                      instance documentation
                    </a>{" "}
                    for more information.
                  </p>
                }
              />
            </Wrapper>
          );
        }

        const assets = assetsOrError.nodes;
        const assetKeys = assetsOrError.nodes.map((x: Asset) => x.key);

        if (!assetKeys.length) {
          return (
            <Wrapper>
              <NonIdealState
                icon="panel-table"
                title="Assets"
                description={
                  <p>
                    There are no known materialized assets with a specified {""}
                    asset key. Any asset keys that have been specified with a
                    <code>Materialization</code> during a pipeline run will
                    appear here. See the{" "}
                    <a href="https://docs.dagster.io/docs/apidocs/solids#dagster.Materialization">
                      Materialization documentation
                    </a>{" "}
                    for more information.
                  </p>
                }
              />
            </Wrapper>
          );
        }
        const assetIsKnown = assetKeys.includes(assetName);

        const topNav = (
          <TabBarContainer>
            <StringSelect
              items={assetKeys}
              itemRenderer={BasicStringRenderer}
              itemListPredicate={BasicStringPredicate}
              noResults={<MenuItem disabled={true} text="No results." />}
              onItemSelect={onSelect}
            >
              <Button
                style={{ minWidth: 200 }}
                text={assetIsKnown ? assetName : "Select an asset..."}
                id="playground-select-pipeline"
                disabled={assetKeys.length === 0}
                rightIcon="double-caret-vertical"
                icon="send-to-graph"
              />
            </StringSelect>
          </TabBarContainer>
        );

        if (!assetName) {
          return (
            <Wrapper>
              <AssetsTable assets={assets} />
            </Wrapper>
          );
        }

        if (!assetIsKnown) {
          return (
            <Wrapper>
              {topNav}
              <NonIdealState
                icon="panel-table"
                title="Assets"
                description={<p>Could not find the asset key `{assetName}`</p>}
              />
            </Wrapper>
          );
        }

        return (
          <Wrapper>
            {topNav}
            <AssetRoot assetKey={assetName} />
          </Wrapper>
        );
      }}
    </Loading>
  );
};

const StringSelect = Select.ofType<string>();
const BasicStringPredicate = (text: string, items: string[]) =>
  items.filter(i => i.toLowerCase().includes(text.toLowerCase())).slice(0, 20);

const BasicStringRenderer = (
  item: string,
  options: { handleClick: any; modifiers: any }
) => (
  <MenuItem
    key={item}
    text={item}
    active={options.modifiers.active}
    onClick={options.handleClick}
  />
);

const AssetsTable = ({ assets }: { assets: Asset[] }) => {
  return (
    <div style={{ margin: 30 }}>
      <Header>Assets</Header>
      <div style={{ marginTop: 30 }}>
        <Legend>
          <LegendColumn>Asset Key</LegendColumn>
          <LegendColumn>Last materialized</LegendColumn>
        </Legend>
        {assets.map((asset: Asset, idx: number) => {
          const timestamp = asset.assetMaterializations.length
            ? new Date(
                parseInt(
                  asset.assetMaterializations[0].materializationEvent.timestamp,
                  10
                )
              ).toLocaleString()
            : "-";
          return (
            <RowContainer key={idx}>
              <RowColumn>
                <Link to={`/assets/${encodeURIComponent(asset.key)}`}>
                  {asset.key}
                </Link>
              </RowColumn>
              <RowColumn>{timestamp}</RowColumn>
            </RowContainer>
          );
        })}
      </div>
    </div>
  );
};

const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  overflow: auto;
`;
const TabBarContainer = styled.div`
  height: 45px;
  display: flex;
  flex-direction: row;
  align-items: center;
  border-bottom: 1px solid ${Colors.GRAY5};
  background: ${Colors.LIGHT_GRAY3};
  padding: 2px 10px;
  z-index: 3;
`;

export const ASSETS_ROOT_QUERY = gql`
  query AssetsRootQuery {
    assetsOrError {
      __typename
      ... on AssetsNotSupportedError {
        message
      }
      ... on AssetConnection {
        nodes {
          key
          assetMaterializations(limit: 1) {
            materializationEvent {
              timestamp
            }
          }
        }
      }
    }
  }
`;
