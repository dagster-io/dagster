import {Colors, Button, ButtonGroup} from '@blueprintjs/core';
import gql from 'graphql-tag';
import {uniq} from 'lodash';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Line, ChartComponentProps} from 'react-chartjs-2';
import styled from 'styled-components';

import {Header, Legend, LegendColumn, RowColumn, RowContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {Timestamp} from 'src/TimeComponents';
import {colorHash} from 'src/Util';
import {AssetPartitionMatrix} from 'src/assets/AssetPartitionMatrix';
import {
  AssetQuery,
  AssetQueryVariables,
  AssetQuery_assetOrError_Asset_lastMaterializations,
  AssetQuery_assetOrError_Asset_historicalMaterializations,
} from 'src/assets/types/AssetQuery';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {MetadataEntries, MetadataEntry} from 'src/runs/MetadataEntry';
import {RunStatus} from 'src/runs/RunStatusDots';
import {RunTable} from 'src/runs/RunTable';
import {titleForRun} from 'src/runs/RunUtils';
import {PipelineRunStatus} from 'src/types/globalTypes';

interface AssetKey {
  path: string[];
}

export const AssetView: React.FunctionComponent<{assetKey: AssetKey}> = ({assetKey}) => {
  const assetPath = assetKey.path.join('.');
  useDocumentTitle(`Asset: ${assetPath}`);

  const queryResult = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
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
              <TitleHeader>Asset: {assetPath}</TitleHeader>
            </Container>
          );
        }

        const lastMaterialization = assetOrError.lastMaterializations[0];
        const partitionsPresent =
          uniq(assetOrError.historicalMaterializations.map((m) => m.partition)).length > 1;

        return (
          <Container>
            <AssetLastMaterialization assetMaterialization={lastMaterialization} />
            {partitionsPresent && (
              <div>
                <Header>Partition Coverage</Header>
                <AssetPartitionMatrix values={assetOrError.historicalMaterializations} />
              </div>
            )}
            <div>
              <Header>Recent Runs</Header>
              <RunTable runs={assetOrError.runs} onSetFilter={(_) => {}} />
            </div>
            <AssetValueGraph
              partitionsPresent={partitionsPresent}
              assetKey={assetKey}
              values={assetOrError.historicalMaterializations}
            />
          </Container>
        );
      }}
    </Loading>
  );
};

const AssetLastMaterialization: React.FunctionComponent<{
  assetMaterialization: AssetQuery_assetOrError_Asset_lastMaterializations;
}> = ({assetMaterialization}) => {
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

const AssetValueGraph: React.FunctionComponent<{
  assetKey: AssetKey;
  partitionsPresent: boolean;
  values: AssetQuery_assetOrError_Asset_historicalMaterializations[];
}> = (props) => {
  const [xAxis, setXAxis] = React.useState<'time' | 'partition'>('time');
  const dataByLabel = {};

  props.values.forEach((graphMaterialization) => {
    const timestamp = graphMaterialization.materializationEvent.timestamp;
    const partition = graphMaterialization.partition;
    if (xAxis === 'partition' && !partition) {
      return;
    }

    graphMaterialization.materializationEvent.materialization.metadataEntries.forEach((entry) => {
      const x = xAxis === 'time' ? parseInt(timestamp, 10) : partition;

      if (entry.__typename === 'EventFloatMetadataEntry') {
        dataByLabel[entry.label] = [
          ...(dataByLabel[entry.label] || []),
          {x: x, y: entry.floatValue},
        ];
      }
      if (entry.__typename === 'EventIntMetadataEntry') {
        dataByLabel[entry.label] = [...(dataByLabel[entry.label] || []), {x: x, y: entry.intValue}];
      }
    });
  });

  if (!Object.keys(dataByLabel).length) {
    return null;
  }

  const graphData: ChartComponentProps['data'] = {
    datasets: Object.keys(dataByLabel).map((label) => ({
      label,
      data: dataByLabel[label],
      borderColor: colorHash(label),
      backgroundColor: 'rgba(0,0,0,0)',
    })),
  };
  const options: ChartComponentProps['options'] = {
    title: {display: true, text: `${props.assetKey.path.join('.')} values`},
    scales: {
      yAxes: [{scaleLabel: {display: true, labelString: 'Value'}}],
      xAxes: [
        xAxis === 'time'
          ? {
              type: 'time',
              scaleLabel: {
                display: true,
                labelString: 'Execution time',
              },
            }
          : {
              type: 'series',
              scaleLabel: {
                display: true,
                labelString: 'Partition Name',
              },
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
      <div style={{display: 'flex'}}>
        <Header>Recent Values</Header>
        <div style={{flex: 1}} />
        <ButtonGroup>
          <Button active={xAxis === 'time'} onClick={() => setXAxis('time')}>
            By Execution Time
          </Button>
          <Button
            active={xAxis === 'partition'}
            onClick={() => setXAxis('partition')}
            disabled={!props.partitionsPresent}
          >
            By Partition
          </Button>
        </ButtonGroup>
      </div>
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

const AssetValueGraphFragment = gql`
  fragment AssetValueGraphFragment on AssetMaterialization {
    materializationEvent {
      timestamp
      materialization {
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
  }
`;

const AssetPartitionGridFragment = gql`
  fragment AssetPartitionGridFragment on AssetMaterialization {
    partition
    runOrError {
      ... on PipelineRun {
        pipelineSnapshotId
      }
    }
  }
`;

export const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        key {
          path
        }
        historicalMaterializations: assetMaterializations {
          ...AssetValueGraphFragment
          ...AssetPartitionGridFragment
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
  ${AssetValueGraphFragment}
  ${AssetPartitionGridFragment}
  ${MetadataEntry.fragments.MetadataEntryFragment}
  ${RunTable.fragments.RunTableRunFragment}
`;
