import {
  Body2,
  Box,
  Caption,
  Colors,
  CursorPaginationControls,
  Icon,
  MiddleTruncate,
  Subtitle1,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import React from 'react';
import {Link} from 'react-router-dom';

import styles from './css/AutomaterializeLeftPanel.module.css';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';
import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';
import {SensorType} from '../../graphql/types';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {numberFormatter} from '../../ui/formatters';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

interface Props extends ListProps {
  evaluations: AssetConditionEvaluationRecordFragment[];
  paginationProps: ReturnType<typeof useEvaluationsQueryResult>['paginationProps'];
}

export const AutomaterializeLeftPanel = ({
  definition,
  evaluations,
  paginationProps,
  onSelectEvaluation,
  selectedEvaluation,
}: Props) => {
  return (
    <Box flex={{direction: 'column', grow: 1}} style={{overflowY: 'auto'}}>
      <AutomaterializeLeftList
        definition={definition}
        evaluations={evaluations}
        onSelectEvaluation={onSelectEvaluation}
        selectedEvaluation={selectedEvaluation}
      />
      {evaluations.length ? (
        <div className={styles.paginationWrapper}>
          <CursorPaginationControls {...paginationProps} />
        </div>
      ) : null}
    </Box>
  );
};

interface ListProps {
  definition?: AssetViewDefinitionNodeFragment | null;
  evaluations: AssetConditionEvaluationRecordFragment[];
  onSelectEvaluation: (evaluation: AssetConditionEvaluationRecordFragment) => void;
  selectedEvaluation?: AssetConditionEvaluationRecordFragment;
}

export const AutomaterializeLeftList = (props: ListProps) => {
  const {evaluations, onSelectEvaluation, selectedEvaluation, definition} = props;

  const sensorName = React.useMemo(
    () =>
      definition?.targetingInstigators.find(
        (instigator) =>
          instigator.__typename === 'Sensor' &&
          (instigator.sensorType === SensorType.AUTO_MATERIALIZE ||
            instigator.sensorType === SensorType.AUTOMATION),
      )?.name,
    [definition],
  );

  const repoAddress = definition
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;

  return (
    <Box flex={{grow: 1, direction: 'column'}}>
      <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
        <Subtitle1>Evaluations</Subtitle1>
      </Box>
      <Box
        padding={{bottom: 8, horizontal: 12}}
        style={{flex: 1, minHeight: 0, overflowY: 'auto'}}
        flex={{grow: 1, direction: 'column'}}
      >
        <Box border="bottom" padding={{top: 8, bottom: 12, left: 12, right: 8}}>
          <Box flex={{alignItems: 'center', gap: 4}}>
            <Icon name="sensors" color={Colors.accentBlue()} />
            <Body2>
              {repoAddress && sensorName ? (
                <Link
                  to={workspacePathFromAddress(repoAddress, `/sensors/${sensorName}`)}
                  style={{maxWidth: 200, overflow: 'hidden'}}
                >
                  <MiddleTruncate text={sensorName} />
                </Link>
              ) : (
                <Link to="/overview/automation">{sensorName ?? 'Automation'}</Link>
              )}
            </Body2>
          </Box>
        </Box>
        <Box flex={{direction: 'column', gap: 8}}>
          {evaluations.length === 0 ? (
            <Box padding={{left: 12, top: 12, right: 8}}>
              <Caption color={Colors.textLight()}>No evaluations</Caption>
            </Box>
          ) : null}
          {evaluations.map((evaluation) => {
            const isSelected = selectedEvaluation?.id === evaluation.id;

            const hasRequested = evaluation.numRequested && evaluation.numRequested > 0;

            function status() {
              if (hasRequested) {
                if (definition?.partitionDefinition) {
                  return (
                    <Caption>
                      {numberFormatter.format(evaluation.numRequested ?? 0)} Requested
                    </Caption>
                  );
                }
                return <Caption>requested</Caption>;
              }
              return <Caption>not requested</Caption>;
            }

            return (
              <button
                key={`skip-${evaluation.id}`}
                className={clsx(
                  styles.evaluationListItem,
                  isSelected && styles.evaluationListItemSelected,
                )}
                onClick={() => {
                  onSelectEvaluation(evaluation);
                }}
              >
                <Box flex={{direction: 'column', gap: 4}}>
                  <Box flex={{direction: 'row', gap: 2, alignItems: 'center'}}>
                    <StatusDot
                      color={
                        evaluation.numRequested ? Colors.accentGreen() : Colors.backgroundDisabled()
                      }
                    />
                    <span style={evaluation.numRequested ? {color: Colors.textGreen()} : undefined}>
                      <TimestampDisplay timestamp={evaluation.timestamp} />
                    </span>
                  </Box>
                  <div style={{paddingLeft: 22}}>{status()}</div>
                </Box>
              </button>
            );
          })}
        </Box>
        <Box border="top" padding={{vertical: 20, horizontal: 12}} margin={{top: 12}}>
          <Caption>Evaluations are retained for 30 days</Caption>
        </Box>
      </Box>
    </Box>
  );
};

export const StatusDot = ({color, size = 10}: {color: string; size?: number}) => (
  <div
    className={styles.statusDot}
    style={{
      backgroundColor: color,
      width: size,
      height: size,
      margin: size / 2,
    }}
  />
);
