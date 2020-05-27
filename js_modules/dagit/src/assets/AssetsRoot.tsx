import * as React from "react";
import styled from "styled-components";
import { Icon, InputGroup, NonIdealState } from "@blueprintjs/core";
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
}>> = ({ match }) => {
  const assetName =
    match.params.assetSelector &&
    decodeURIComponent(match.params.assetSelector);
  const queryResult = useQuery(ASSETS_ROOT_QUERY);

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
          <div style={{ margin: 20 }}>
            <Link to="/assets">
              <Icon icon="chevron-left" /> Back to Assets
            </Link>
          </div>
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

const matches = (haystack: string, needle: string) =>
  needle
    .toLowerCase()
    .split(" ")
    .filter(x => x)
    .every(word => haystack.toLowerCase().includes(word));

const AssetsTable = ({ assets }: { assets: Asset[] }) => {
  const [q, setQ] = React.useState<string>("");
  return (
    <div style={{ margin: 30 }}>
      <Header>Assets</Header>
      <div style={{ marginTop: 30 }}>
        <InputGroup
          type="text"
          value={q}
          small
          placeholder={`Search asset_keys...`}
          onChange={(e: React.ChangeEvent<any>) => setQ(e.target.value)}
          style={{ marginBottom: 20 }}
        />
        <Legend>
          <LegendColumn>Asset Key</LegendColumn>
          <LegendColumn>Last materialized</LegendColumn>
        </Legend>
        {assets
          .filter((asset: Asset) => !q || matches(asset.key, q))
          .map((asset: Asset, idx: number) => {
            const timestamp = asset.assetMaterializations.length
              ? new Date(
                  parseInt(
                    asset.assetMaterializations[0].materializationEvent
                      .timestamp,
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
