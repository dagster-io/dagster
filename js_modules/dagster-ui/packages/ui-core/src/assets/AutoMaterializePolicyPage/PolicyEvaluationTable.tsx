import {Box, Colors, Table} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import styled, {css} from 'styled-components';

import {PartitionSegmentWithPopover} from './PartitionSegmentWithPopover';
import {PolicyEvaluationCondition} from './PolicyEvaluationCondition';
import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';
import {flattenEvaluations} from './flattenEvaluations';
import {
  AssetConditionEvaluation,
  AssetConditionEvaluationStatus,
  PartitionedAssetConditionEvaluation,
  SpecificPartitionAssetConditionEvaluation,
  UnpartitionedAssetConditionEvaluation,
} from './types';
import {assertUnreachable} from '../../app/Util';
import {TimeElapsed} from '../../runs/TimeElapsed';

interface Props<T> {
  rootEvaluation: T;
}

export const PolicyEvaluationTable = <T extends AssetConditionEvaluation>({
  rootEvaluation,
}: Props<T>) => {
  switch (rootEvaluation.__typename) {
    case 'UnpartitionedAssetConditionEvaluation':
    case 'SpecificPartitionAssetConditionEvaluation':
      return <UnpartitionedPolicyEvaluationTable rootEvaluation={rootEvaluation} />;
    case 'PartitionedAssetConditionEvaluation':
      return <PartitionedPolicyEvaluationTable rootEvaluation={rootEvaluation} />;
    default:
      return assertUnreachable(rootEvaluation);
  }
};

const UnpartitionedPolicyEvaluationTable = ({
  rootEvaluation,
}: {
  rootEvaluation: UnpartitionedAssetConditionEvaluation | SpecificPartitionAssetConditionEvaluation;
}) => {
  const [hoveredKey, setHoveredKey] = useState<number | null>(null);
  const flattened = useMemo(() => flattenEvaluations(rootEvaluation), [rootEvaluation]);
  const showDuration = rootEvaluation.__typename === 'UnpartitionedAssetConditionEvaluation';
  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          {showDuration ? <th>Duration</th> : null}
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {flattened.map(({evaluation, id, parentId, depth, type}) => {
          const {description, status} = evaluation;
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
                <PolicyEvaluationStatusTag status={status} />
              </td>
              {showDuration ? (
                <td>
                  {evaluation.__typename === 'UnpartitionedAssetConditionEvaluation' ? (
                    <TimeElapsed
                      startUnix={evaluation.startTimestamp}
                      endUnix={evaluation.endTimestamp}
                    />
                  ) : null}
                </td>
              ) : null}
              <td></td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const FULL_SEGMENTS_WIDTH = 200;

const PartitionedPolicyEvaluationTable = ({
  rootEvaluation,
}: {
  rootEvaluation: PartitionedAssetConditionEvaluation;
}) => {
  const [hoveredKey, setHoveredKey] = useState<number | null>(null);
  const flattened = useMemo(() => flattenEvaluations(rootEvaluation), [rootEvaluation]);
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
          const {
            description,
            endTimestamp,
            startTimestamp,
            numTrue,
            numFalse,
            numSkipped,
            trueSubset,
            falseSubset,
            candidateSubset,
          } = evaluation;
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
                    <PartitionSegmentWithPopover
                      description={description}
                      status={AssetConditionEvaluationStatus.TRUE}
                      subset={trueSubset}
                      width={Math.ceil((numTrue / total) * FULL_SEGMENTS_WIDTH)}
                    />
                  ) : null}
                  {numFalse > 0 ? (
                    <PartitionSegmentWithPopover
                      status={AssetConditionEvaluationStatus.FALSE}
                      description={description}
                      subset={falseSubset}
                      width={Math.ceil((numFalse / total) * FULL_SEGMENTS_WIDTH)}
                    />
                  ) : null}
                  {numSkipped > 0 ? (
                    <PartitionSegmentWithPopover
                      status={AssetConditionEvaluationStatus.SKIPPED}
                      description={description}
                      subset={candidateSubset}
                      width={Math.ceil((numSkipped / total) * FULL_SEGMENTS_WIDTH)}
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
      inset 1px 1px 0 ${Colors.keylineDefault()},
      inset -1px 0 0 ${Colors.keylineDefault()} !important;
  }

  & tr:last-child td:last-child {
    box-shadow:
      inset -1px -1px 0 ${Colors.keylineDefault()},
      inset 1px 1px 0 ${Colors.keylineDefault()} !important;
  }
`;

type RowHighlightType = 'hovered' | 'highlighted' | 'none';

const EvaluationRow = styled.tr<{$highlight: RowHighlightType}>`
  background-color: ${({$highlight}) => {
    switch ($highlight) {
      case 'hovered':
        return Colors.backgroundLightHover();
      case 'highlighted':
        return Colors.backgroundDefaultHover();
      case 'none':
        return Colors.backgroundDefault();
    }
  }};

  ${({$highlight}) => {
    if ($highlight === 'hovered') {
      return css`
        && td {
          box-shadow:
            inset 0 -1px 0 ${Colors.keylineDefault()},
            inset 1px 1px 0 ${Colors.keylineDefault()} !important;
        }

        && td:last-child {
          box-shadow:
            inset -1px -1px 0 ${Colors.keylineDefault()},
            inset 1px 1px 0 ${Colors.keylineDefault()} !important;
        }
      `;
    }
    return '';
  }}
`;
