import * as React from 'react';
import styled from 'styled-components';
import gql from 'graphql-tag';
import {Colors} from '@blueprintjs/core';
import {useQuery} from 'react-apollo';
import Loading from '../Loading';
import {Timestamp} from '../TimeComponents';
import {AssetsRootQuery_assetsOrError_AssetConnection_nodes_key} from './types/AssetsRootQuery';
import {
  AssetQuery_assetOrError_Asset_graphMaterializations,
  AssetQuery_assetOrError_Asset_lastMaterializations,
} from './types/AssetQuery';
import {Header, Legend, LegendColumn, RowContainer, RowColumn} from '../ListComponents';
import {MetadataEntries, MetadataEntry} from '../runs/MetadataEntry';
import {RunTable} from '../runs/RunTable';
import {RunStatus} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {PipelineRunStatus} from '../types/globalTypes';
import {Line} from 'react-chartjs-2';
import {colorHash} from '../Util';

type AssetKey = AssetsRootQuery_assetsOrError_AssetConnection_nodes_key;
type GraphMaterialization = AssetQuery_assetOrError_Asset_graphMaterializations;
type LastMaterialization = AssetQuery_assetOrError_Asset_lastMaterializations;

export const AssetRoot = ({assetKey}: {assetKey: AssetKey}) => {
  const queryResult = useQuery(ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
  });
  return (
    <Loading queryResult={queryResult}>
      {({assetOrError}) => {
        if (assetOrError.__typename !== 'Asset') {
          return null;
        }
        if (!assetOrError.lastMaterializations.length) {
          return (
            <Container>
              <TitleHeader>Asset: {assetKey.path.join('.')}</TitleHeader>
            </Container>
          );
        }

        const lastMaterialization = assetOrError.lastMaterializations[0];
        return (
          <Container>
            <TitleHeader>Asset: {assetKey.path.join('.')}</TitleHeader>
            <AssetLastMaterialization assetMaterialization={lastMaterialization} />
            <div>
              <Header>Recent Runs</Header>
              <RunTable runs={assetOrError.runs} onSetFilter={(_) => {}} />
            </div>
            <AssetValueGraph assetKey={assetKey} values={assetOrError.graphMaterializations} />
          </Container>
        );
      }}
    </Loading>
  );
};

const AssetLastMaterialization = ({
  assetMaterialization,
}: {
  assetMaterialization: LastMaterialization;
}) => {
  const run =
    assetMaterialization.runOrError.__typename === 'PipelineRun'
      ? assetMaterialization.runOrError
      : undefined;
  const {runId, materialization, timestamp} = assetMaterialization.materializationEvent;
  const metadataEntries = materialization.metadataEntries;
  return (
    <Section>
      <Header>Last Materialization Event</Header>
      <div>
        <Legend>
          <LegendColumn style={{maxWidth: 30}}></LegendColumn>
          <LegendColumn style={{maxWidth: 250}}>Run</LegendColumn>
          <LegendColumn style={{flex: 2}}>Materialization</LegendColumn>
          <LegendColumn style={{flex: 3}}>Details</LegendColumn>
          <LegendColumn style={{maxWidth: 300}}>Timestamp</LegendColumn>
        </Legend>

        <RowContainer>
          <RowColumn style={{maxWidth: 30, paddingLeft: 0, textAlign: 'center'}}>
            {run ? (
              <RunStatus status={run.status} />
            ) : (
              <RunStatus status={PipelineRunStatus.NOT_STARTED} />
            )}
          </RowColumn>
          <RowColumn style={{maxWidth: 250}}>
            {run ? (
              <a href={`/pipeline/${run.pipelineName}/runs/${run.runId}`}>{titleForRun(run)}</a>
            ) : (
              runId
            )}
          </RowColumn>
          <RowColumn style={{flex: 2}}>
            {materialization.label}
            {materialization.description ? (
              <div style={{fontSize: '0.8rem', marginTop: 10}}>{materialization.description}</div>
            ) : null}
          </RowColumn>
          <RowColumn style={{flex: 3, fontSize: 12}}>
            {metadataEntries && metadataEntries.length ? (
              <MetadataEntries entries={metadataEntries} />
            ) : null}
          </RowColumn>
          <RowColumn style={{maxWidth: 300}}>
            <Timestamp ms={parseInt(timestamp)} />
          </RowColumn>
        </RowContainer>
      </div>
    </Section>
  );
};

const AssetValueGraph = (props: any) => {
  const dataByLabel = {};
  props.values.forEach((graphMaterialization: GraphMaterialization) => {
    const timestamp = graphMaterialization.materializationEvent.timestamp;
    graphMaterialization.materializationEvent.materialization.metadataEntries.forEach((entry) => {
      if (entry.__typename === 'EventFloatMetadataEntry') {
        dataByLabel[entry.label] = [
          ...(dataByLabel[entry.label] || []),
          {x: parseInt(timestamp, 10), y: entry.value},
        ];
      }
    });
  });

  if (!Object.keys(dataByLabel).length) {
    return null;
  }

  const graphData = {
    datasets: Object.keys(dataByLabel).map((label) => ({
      label,
      data: dataByLabel[label],
      borderColor: colorHash(label),
      backgroundColor: 'rgba(0,0,0,0)',
    })),
  };
  const options = {
    title: {display: true, text: `${props.assetKey.path.join('.')} values`},
    scales: {
      yAxes: [{scaleLabel: {display: true, labelString: 'Value'}}],
      xAxes: [
        {
          type: 'time',
          scaleLabel: {display: true, labelString: 'Execution time'},
        },
      ],
    },
    legend: {
      display: false,
      onClick: (_e: MouseEvent, _legendItem: any) => {},
    },
  };
  return (
    <div style={{marginTop: 30}}>
      <Header>Recent Values</Header>
      <Line data={graphData} height={100} options={options} />
    </div>
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
  query AssetQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        key {
          path
        }
        graphMaterializations: assetMaterializations {
          materializationEvent {
            timestamp
            materialization {
              metadataEntries {
                ...MetadataEntryFragment
              }
            }
          }
        }
        lastMaterializations: assetMaterializations(limit: 1) {
          runOrError {
            ... on PipelineRun {
              runId
              status
              pipelineName
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

        runs(limit: 10) {
          ...RunTableRunFragment
        }
      }
    }
  }
  ${MetadataEntry.fragments.MetadataEntryFragment}
  ${RunTable.fragments.RunTableRunFragment}
`;
