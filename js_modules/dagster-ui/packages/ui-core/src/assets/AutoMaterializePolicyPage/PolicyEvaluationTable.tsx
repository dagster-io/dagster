import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Table,
  colorBackgroundDefault,
  colorBackgroundDefaultHover,
  colorBackgroundLightHover,
  colorKeylineDefault,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled, {css} from 'styled-components';

import {AssetConditionEvaluationStatus} from '../../graphql/types';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

import {PartitionSegmentWithPopover} from './PartitionSegmentWithPopover';
import {PolicyEvaluationCondition} from './PolicyEvaluationCondition';
import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';
import {FlattenedConditionEvaluation, flattenEvaluations} from './flattenEvaluations';
import {
  AssetConditionEvaluationRecordFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';
import {
  FullPartitionsQuery,
  FullPartitionsQueryVariables,
} from './types/PolicyEvaluationTable.types';

interface Props {
  evaluationRecord: Pick<AssetConditionEvaluationRecordFragment, 'evaluation'>;
  definition?: AssetViewDefinitionNodeFragment | null;
  selectPartition: (partitionKey: string | null) => void;
}

export const PolicyEvaluationTable = ({evaluationRecord, definition, selectPartition}: Props) => {
  const flattened = React.useMemo(() => flattenEvaluations(evaluationRecord), [evaluationRecord]);
  if (flattened[0]?.evaluation.__typename === 'PartitionedAssetConditionEvaluationNode') {
    return (
      <PartitionedPolicyEvaluationTable
        flattenedRecords={
          flattened as FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[]
        }
        definition={definition}
        selectPartition={selectPartition}
      />
    );
  }

  return (
    <UnpartitionedPolicyEvaluationTable
      flattenedRecords={
        flattened as
          | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>[]
          | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>[]
      }
    />
  );
};

const UnpartitionedPolicyEvaluationTable = ({
  flattenedRecords,
}: {
  flattenedRecords:
    | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>[]
    | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>[];
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);
  const isSpecificPartitionAssetConditionEvaluations =
    flattenedRecords[0]?.evaluation.__typename === 'SpecificPartitionAssetConditionEvaluationNode';
  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          {isSpecificPartitionAssetConditionEvaluations ? null : <th>Duration</th>}
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
          const {description, status} = evaluation;
          let endTimestamp, startTimestamp;
          if ('endTimestamp' in evaluation) {
            endTimestamp = evaluation.endTimestamp;
            startTimestamp = evaluation.startTimestamp;
          }
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
              {startTimestamp && endTimestamp ? (
                <td>
                  <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} />
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
  flattenedRecords,
  definition,
  selectPartition,
}: {
  flattenedRecords: FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[];
  definition?: AssetViewDefinitionNodeFragment | null;
  selectPartition: (partitionKey: string | null) => void;
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);

  const {data} = useQuery<FullPartitionsQuery, FullPartitionsQueryVariables>(
    FULL_PARTITIONS_QUERY,
    {
      variables: definition
        ? {
            assetKey: {path: definition.assetKey.path},
          }
        : undefined,
      skip: !definition?.assetKey,
    },
  );

  // let partitionKeys = null;
  // if (data?.assetNodeOrError.__typename === 'AssetNode') {
  //   partitionKeys = data.assetNodeOrError.partitionKeysByDimension;
  // }

  // Fetch partitions
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
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
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
                      selectPartition={selectPartition}
                    />
                  ) : null}
                  {numFalse > 0 ? (
                    <PartitionSegmentWithPopover
                      status={AssetConditionEvaluationStatus.FALSE}
                      description={description}
                      subset={falseSubset}
                      width={Math.ceil((numFalse / total) * FULL_SEGMENTS_WIDTH)}
                      selectPartition={selectPartition}
                    />
                  ) : null}
                  {numSkipped > 0 ? (
                    <PartitionSegmentWithPopover
                      status={AssetConditionEvaluationStatus.SKIPPED}
                      description={description}
                      subset={candidateSubset}
                      width={Math.ceil((numSkipped / total) * FULL_SEGMENTS_WIDTH)}
                      selectPartition={selectPartition}
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

const FULL_PARTITIONS_QUERY = gql`
  query FullPartitionsQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeysByDimension {
          name
          type
          partitionKeys
        }
      }
    }
  }
`;
