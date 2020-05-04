import * as React from "react";
import styled from "styled-components";
import gql from "graphql-tag";
import { Colors } from "@blueprintjs/core";
import { useQuery } from "react-apollo";
import Loading from "../Loading";
import { AssetQuery_assetOrError_Asset_assetMaterializations } from "./types/AssetQuery";
import { Header, RowContainer, RowColumn } from "../ListComponents";
import { MetadataEntries, MetadataEntry } from "../runs/MetadataEntry";

type AssetMaterialization = AssetQuery_assetOrError_Asset_assetMaterializations;

export const AssetRoot = ({ assetKey }: { assetKey: string }) => {
  const queryResult = useQuery(ASSET_QUERY, {
    variables: { assetKey }
  });
  return (
    <Loading queryResult={queryResult}>
      {({ assetOrError }) => {
        if (assetOrError.__typename !== "Asset") {
          return null;
        }
        return (
          <Container>
            <TitleHeader>Asset: {assetKey}</TitleHeader>
            {assetOrError.assetMaterializations.length ? (
              <AssetMaterialization
                assetMaterialization={assetOrError.assetMaterializations[0]}
              />
            ) : null}
          </Container>
        );
      }}
    </Loading>
  );
};

const AssetMaterialization = ({
  assetMaterialization
}: {
  assetMaterialization: AssetMaterialization;
}) => {
  const run =
    assetMaterialization.runOrError.__typename === "PipelineRun"
      ? assetMaterialization.runOrError
      : undefined;
  const {
    runId,
    materialization,
    timestamp
  } = assetMaterialization.materializationEvent;
  const metadataEntries = materialization.metadataEntries;
  return (
    <div>
      <Header>Last Materialized Event</Header>
      <TableContainer>
        <RowContainer>
          <RowColumn>Run</RowColumn>
          <RowColumn>Label</RowColumn>
          <RowColumn>Description</RowColumn>
          <RowColumn>Timestamp</RowColumn>
          <RowColumn>Details</RowColumn>
        </RowContainer>

        <RowContainer>
          <RowColumn>
            {run ? (
              <a href={`/runs/${run.pipeline.name}/${run.runId}`}>{runId}</a>
            ) : (
              runId
            )}
          </RowColumn>
          <RowColumn>{materialization.label}</RowColumn>
          <RowColumn>{materialization.description || "-"}</RowColumn>
          <RowColumn>
            {new Date(parseInt(timestamp)).toLocaleString()}
          </RowColumn>
          <RowColumn>
            {metadataEntries && metadataEntries.length ? (
              <MetadataEntries entries={metadataEntries} />
            ) : null}
          </RowColumn>
        </RowContainer>
      </TableContainer>
    </div>
  );
};

const TableContainer = styled.div``;
const TitleHeader = styled.div`
  color: ${Colors.BLACK};
  font-size: 1.3rem;
  margin-bottom: 30px;
`;
const Container = styled.div`
  margin: 20px;
`;

export const ASSET_QUERY = gql`
  query AssetQuery($assetKey: String!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        key
        assetMaterializations(limit: 1) {
          runOrError {
            ... on PipelineRun {
              runId
              status
              pipeline {
                name
              }
            }
          }
          materializationEvent {
            runId
            timestamp
            materialization {
              label
              description
              metadataEntries {
                ...MetadataEntryFragment
              }
            }
          }
        }
      }
    }
  }
  ${MetadataEntry.fragments.MetadataEntryFragment}
`;
