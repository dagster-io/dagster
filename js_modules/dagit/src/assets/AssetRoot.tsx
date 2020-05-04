import * as React from "react";
import styled from "styled-components";
import gql from "graphql-tag";
import { Colors } from "@blueprintjs/core";
import { useQuery } from "react-apollo";
import Loading from "../Loading";
import { AssetQuery_assetOrError_Asset_assetMaterializations } from "./types/AssetQuery";
import {
  Header,
  Legend,
  LegendColumn,
  RowContainer,
  RowColumn
} from "../ListComponents";
import { MetadataEntries, MetadataEntry } from "../runs/MetadataEntry";
import { RunTable } from "../runs/RunTable";
import { RunStatus, titleForRun } from "../runs/RunUtils";
import { PipelineRunStatus } from "../types/globalTypes";

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
        if (!assetOrError.assetMaterializations.length) {
          return (
            <Container>
              <TitleHeader>Asset: {assetKey}</TitleHeader>
            </Container>
          );
        }

        const lastMaterialization = assetOrError.assetMaterializations[0];
        return (
          <Container>
            <TitleHeader>Asset: {assetKey}</TitleHeader>
            <AssetLastMaterialization
              assetMaterialization={lastMaterialization}
            />
            <div>
              <Header>Recent Runs</Header>
              <RunTable runs={assetOrError.runs} onSetFilter={_ => {}} />
            </div>
          </Container>
        );
      }}
    </Loading>
  );
};

const AssetLastMaterialization = ({
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
    <Section>
      <Header>Last Materialized Event</Header>
      <div>
        <Legend>
          <LegendColumn style={{ maxWidth: 30 }}></LegendColumn>
          <LegendColumn style={{ maxWidth: 250 }}>Run</LegendColumn>
          <LegendColumn>Materialization</LegendColumn>
          <LegendColumn>Details</LegendColumn>
          <LegendColumn style={{ maxWidth: 400 }}>Timestamp</LegendColumn>
        </Legend>

        <RowContainer>
          <RowColumn
            style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}
          >
            {run ? (
              <RunStatus status={run.status} />
            ) : (
              <RunStatus status={PipelineRunStatus.NOT_STARTED} />
            )}
          </RowColumn>
          <RowColumn style={{ maxWidth: 250 }}>
            {run ? (
              <a href={`/runs/${run.pipeline.name}/${run.runId}`}>
                {titleForRun(run)}
              </a>
            ) : (
              runId
            )}
          </RowColumn>
          <RowColumn>
            {materialization.label}
            {materialization.description ? (
              <div style={{ fontSize: "0.8rem", marginTop: 10 }}>
                {materialization.description}
              </div>
            ) : null}
          </RowColumn>
          <RowColumn>
            {metadataEntries && metadataEntries.length ? (
              <MetadataEntries entries={metadataEntries} />
            ) : null}
          </RowColumn>
          <RowColumn style={{ maxWidth: 400 }}>
            {new Date(parseInt(timestamp)).toLocaleString()}
          </RowColumn>
        </RowContainer>
      </div>
    </Section>
  );
};

const Section = styled.div`
  margin-bottom: 30px;
`;
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
        runs {
          ...RunTableRunFragment
        }
      }
    }
  }
  ${MetadataEntry.fragments.MetadataEntryFragment}
  ${RunTable.fragments.RunTableRunFragment}
`;
