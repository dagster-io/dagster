import {
  Box,
  Table,
  Tag,
  colorAccentGray,
  colorAccentGreen,
  colorAccentYellow,
  colorBackgroundDefault,
  colorBackgroundDefaultHover,
  colorBackgroundLightHover,
  colorKeylineDefault,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled, {css} from 'styled-components';

import {assertUnreachable} from '../../app/Util';
import {TimeElapsed} from '../../runs/TimeElapsed';

import {PolicyEvaluationCondition} from './PolicyEvaluationCondition';
import {flattenEvaluations} from './flattenEvaluations';
import {
  AssetConditionEvaluation,
  AssetConditionEvaluationStatus,
  PartitionedAssetConditionEvaluation,
  UnpartitionedAssetConditionEvaluation,
} from './types';

interface Props<T> {
  rootEvaluation: T;
}

export const PolicyEvaluationTable = <T extends AssetConditionEvaluation>({
  rootEvaluation,
}: Props<T>) => {
  if (rootEvaluation.__typename === 'UnpartitionedAssetConditionEvaluation') {
    return <UnpartitionedPolicyEvaluationTable rootEvaluation={rootEvaluation} />;
  }

  return <PartitionedPolicyEvaluationTable rootEvaluation={rootEvaluation} />;
};

const UnpartitionedPolicyEvaluationTable = ({
  rootEvaluation,
}: {
  rootEvaluation: UnpartitionedAssetConditionEvaluation;
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);
  const flattened = React.useMemo(() => flattenEvaluations(rootEvaluation), [rootEvaluation]);
  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          <th>Duration</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {flattened.map(({evaluation, id, parentId, depth, type}) => {
          const {description, endTimestamp, startTimestamp, status} = evaluation;
          return (
            <EvaluationRow
              key={id}
              $highlight={
                hoveredKey === id ? 'hovered' : parentId === hoveredKey ? 'highlighted' : 'none'
              }
              onMouseEnter={() => setHoveredKey(id)}
              onMouseLeave={() => setHoveredKey(null)}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={type === 'group' ? 'resource' : 'wysiwyg'}
                  label={description}
                  skipped={status === AssetConditionEvaluationStatus.SKIPPED}
                  depth={depth}
                  type={type}
                />
              </td>
              <td>
                <EvaluationStatusTag status={status} />
              </td>
              <td>
                <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} />
              </td>
              <td></td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const EvaluationStatusTag = ({status}: {status: AssetConditionEvaluationStatus}) => {
  switch (status) {
    case AssetConditionEvaluationStatus.FALSE:
      return (
        <Tag intent="warning" icon="cancel">
          False
        </Tag>
      );
    case AssetConditionEvaluationStatus.TRUE:
      return (
        <Tag intent="success" icon="check_circle">
          True
        </Tag>
      );
    case AssetConditionEvaluationStatus.SKIPPED:
      return <Tag intent="none">Skipped</Tag>;
    default:
      return assertUnreachable(status);
  }
};

const FULL_SEGMENTS_WIDTH = 200;

const PartitionedPolicyEvaluationTable = ({
  rootEvaluation,
}: {
  rootEvaluation: PartitionedAssetConditionEvaluation;
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);
  const flattened = React.useMemo(() => flattenEvaluations(rootEvaluation), [rootEvaluation]);
  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {flattened.map(({evaluation, id, parentId, depth, type}) => {
          const {description, endTimestamp, startTimestamp, numTrue, numFalse, numSkipped} =
            evaluation;
          const total = numTrue + numFalse + numSkipped;

          return (
            <EvaluationRow
              key={id}
              $highlight={
                hoveredKey === id ? 'hovered' : parentId === hoveredKey ? 'highlighted' : 'none'
              }
              onMouseEnter={() => setHoveredKey(id)}
              onMouseLeave={() => setHoveredKey(null)}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={type === 'group' ? 'resource' : 'wysiwyg'}
                  label={description}
                  depth={depth}
                  type={type}
                />
              </td>
              <td style={{width: 0}}>
                <Box
                  flex={{direction: 'row', alignItems: 'center', gap: 2}}
                  style={{width: FULL_SEGMENTS_WIDTH}}
                >
                  {numTrue > 0 ? (
                    <PartitionSegment
                      $color={colorAccentGreen()}
                      $width={Math.ceil((numTrue / total) * FULL_SEGMENTS_WIDTH)}
                    />
                  ) : null}
                  {numFalse > 0 ? (
                    <PartitionSegment
                      $color={colorAccentYellow()}
                      $width={Math.ceil((numFalse / total) * FULL_SEGMENTS_WIDTH)}
                    />
                  ) : null}
                  {numSkipped > 0 ? (
                    <PartitionSegment
                      $color={colorAccentGray()}
                      $width={Math.ceil((numSkipped / total) * FULL_SEGMENTS_WIDTH)}
                    />
                  ) : null}
                </Box>
              </td>
              <td>
                <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} />
              </td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const VeryCompactTable = styled(Table)`
  & tr td {
    vertical-align: middle;
  }

  & tr td:first-child {
    padding: 2px 16px;
  }

  & tr th:last-child,
  & tr td:last-child {
    box-shadow:
      inset 1px 1px 0 ${colorKeylineDefault()},
      inset -1px 0 0 ${colorKeylineDefault()} !important;
  }

  & tr:last-child td:last-child {
    box-shadow:
      inset -1px -1px 0 ${colorKeylineDefault()},
      inset 1px 1px 0 ${colorKeylineDefault()} !important;
  }
`;

type RowHighlightType = 'hovered' | 'highlighted' | 'none';

const EvaluationRow = styled.tr<{$highlight: RowHighlightType}>`
  background-color: ${({$highlight}) => {
    switch ($highlight) {
      case 'hovered':
        return colorBackgroundLightHover();
      case 'highlighted':
        return colorBackgroundDefaultHover();
      case 'none':
        return colorBackgroundDefault();
    }
  }};

  ${({$highlight}) => {
    if ($highlight === 'hovered') {
      return css`
        && td {
          box-shadow:
            inset 0 -1px 0 ${colorKeylineDefault()},
            inset 1px 1px 0 ${colorKeylineDefault()} !important;
        }

        && td:last-child {
          box-shadow:
            inset -1px -1px 0 ${colorKeylineDefault()},
            inset 1px 1px 0 ${colorKeylineDefault()} !important;
        }
      `;
    }
    return '';
  }}
`;

interface PartitionSegmentProps {
  $color: string;
  $width: number;
}

const PartitionSegment = styled.div.attrs<PartitionSegmentProps>(({$width}) => ({
  style: {
    flexBasis: `${$width}px`,
  },
}))<PartitionSegmentProps>`
  background-color: ${({$color}) => $color};
  border-radius: 2px;
  height: 20px;
`;
