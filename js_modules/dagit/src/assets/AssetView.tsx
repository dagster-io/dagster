import {Colors, Button, ButtonGroup} from '@blueprintjs/core';
import gql from 'graphql-tag';
import {uniq} from 'lodash';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Line, ChartComponentProps} from 'react-chartjs-2';
import styled from 'styled-components';

import {Header} from 'src/ListComponents';
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
import {Table} from 'src/ui/Table';
import {FontFamily} from 'src/ui/styles';

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
      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{width: '32px'}}></th>
            <th style={{maxWidth: '80px'}}>Run</th>
            <th style={{width: '20%'}}>Materialization</th>
            <th style={{width: '100%'}}>Details</th>
            <th style={{maxWidth: 300}}>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              {run ? (
                <RunStatus status={run.status} />
              ) : (
                <RunStatus status={PipelineRunStatus.NOT_STARTED} />
              )}
            </td>
            <td style={{fontFamily: FontFamily.monospace}}>
              {run ? (
                <a href={`/pipeline/${run.pipelineName}/runs/${run.runId}`}>{titleForRun(run)}</a>
              ) : (
                runId
              )}
            </td>
            <td>
              {materialization.label}
              {materialization.description ? (
                <div style={{fontSize: '0.8rem', marginTop: 10}}>{materialization.description}</div>
              ) : null}
            </td>
            <td style={{fontSize: 12}}>
              {metadataEntries && metadataEntries.length ? (
                <MetadataEntries entries={metadataEntries} />
              ) : null}
            </td>
            <td>
              <Timestamp ms={parseInt(timestamp)} />
            </td>
          </tr>
        </tbody>
      </Table>
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
