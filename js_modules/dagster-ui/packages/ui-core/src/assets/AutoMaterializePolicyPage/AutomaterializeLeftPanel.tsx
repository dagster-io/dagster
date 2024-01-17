import {
  Body2,
  Box,
  Caption,
  CursorPaginationControls,
  Icon,
  MiddleTruncate,
  Subtitle1,
  colorAccentBlue,
  colorAccentGreen,
  colorBackgroundBlue,
  colorBackgroundBlueHover,
  colorBackgroundDefault,
  colorBackgroundDefaultHover,
  colorBackgroundDisabled,
  colorBackgroundLight,
  colorKeylineDefault,
  colorTextBlue,
  colorTextDefault,
  colorTextGreen,
  colorTextLight,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {SensorType} from '../../graphql/types';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {numberFormatter} from '../../ui/formatters';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';
import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';

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
        <PaginationWrapper>
          <CursorPaginationControls {...paginationProps} />
        </PaginationWrapper>
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
          instigator.sensorType === SensorType.AUTOMATION_POLICY,
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
            <Icon name="sensors" color={colorAccentBlue()} />
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
        <Box flex={{direction: 'column'}}>
          {evaluations.length === 0 ? (
            <Caption color={colorTextLight()}>No evaluations</Caption>
          ) : null}
          {evaluations.map((evaluation) => {
            const isSelected = selectedEvaluation?.id === evaluation.id;

            const hasRequested = evaluation.numRequested > 0;

            function status() {
              if (hasRequested) {
                if (definition?.partitionDefinition) {
                  return (
                    <Caption>{numberFormatter.format(evaluation.numRequested)} Requested</Caption>
                  );
                }
                return <Caption>requested</Caption>;
              }
              return <Caption>not requested</Caption>;
            }

            return (
              <EvaluationListItem
                key={`skip-${evaluation.id}`}
                onClick={() => {
                  onSelectEvaluation(evaluation);
                }}
                $selected={isSelected}
              >
                <Box flex={{direction: 'column', gap: 4}}>
                  <Box flex={{direction: 'row', gap: 2, alignItems: 'center'}}>
                    <StatusDot
                      $color={
                        evaluation.numRequested ? colorAccentGreen() : colorBackgroundDisabled()
                      }
                    />
                    <span style={evaluation.numRequested ? {color: colorTextGreen()} : undefined}>
                      <TimestampDisplay timestamp={evaluation.timestamp} />
                    </span>
                  </Box>
                  <div style={{paddingLeft: 22}}>{status()}</div>
                </Box>
              </EvaluationListItem>
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

const PaginationWrapper = styled.div`
  position: sticky;
  bottom: 0;
  background: ${colorBackgroundLight()};
  border-right: 1px solid ${colorKeylineDefault()};
  box-shadow: inset 0 1px ${colorKeylineDefault()};
  margin-top: -1px;
  padding-bottom: 16px;
  padding-top: 16px;
  > * {
    margin-top: 0;
  }
`;

interface EvaluationListItemProps {
  $selected: boolean;
}

const EvaluationListItem = styled.button<EvaluationListItemProps>`
  background-color: ${({$selected}) =>
    $selected ? colorBackgroundBlue() : colorBackgroundDefault()};
  border: none;
  border-radius: 8px;
  color: ${({$selected}) => ($selected ? colorTextBlue() : colorTextDefault())};
  cursor: pointer;
  margin: 2px 0;
  text-align: left;
  transition:
    100ms background-color linear,
    100ms color linear;
  user-select: none;

  &:hover {
    background-color: ${({$selected}) =>
      $selected ? colorBackgroundBlueHover() : colorBackgroundDefaultHover()};
  }

  &:focus,
  &:active {
    outline: none;
  }

  padding: 8px 12px;
`;

export const StatusDot = styled.div<{$color: string}>`
  background-color: ${({$color}) => $color};
  border-radius: 50%;
  width: 10px;
  height: 10px;
  margin: 5px;
`;
