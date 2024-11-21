import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  Table,
  Tooltip,
} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';
import styled, {css} from 'styled-components';

import {EvaluationConditionalLabel, EvaluationUserLabel} from './EvaluationConditionalLabel';
import {PartitionSegmentWithPopover} from './PartitionSegmentWithPopover';
import {PolicyEvaluationCondition} from './PolicyEvaluationCondition';
import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';
import {Evaluation, FlattenedConditionEvaluation, flattenEvaluations} from './flattenEvaluations';
import {
  NewEvaluationNodeFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';
import {AssetConditionEvaluationStatus} from '../../graphql/types';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntryFragment.types';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {numberFormatter} from '../../ui/formatters';
import {AssetEventMetadataEntriesTable} from '../AssetEventMetadataEntriesTable';

interface Props {
  assetKeyPath: string[] | null;
  evaluationNodes: Evaluation[];
  evaluationId: string;
  rootUniqueId: string;
  isLegacyEvaluation: boolean;
  selectPartition: (partitionKey: string | null) => void;
}

export const PolicyEvaluationTable = (props: Props) => {
  const {
    assetKeyPath,
    evaluationNodes,
    evaluationId,
    rootUniqueId,
    isLegacyEvaluation,
    selectPartition,
  } = props;
  const [expandedRecords, setExpandedRecords] = useState<Set<string>>(() => {
    const list = isLegacyEvaluation ? evaluationNodes.map((node) => node.uniqueId) : [];
    return new Set(list);
  });

  const flattened = useMemo(() => {
    return flattenEvaluations({
      evaluationNodes,
      rootUniqueId,
      expandedRecords,
    });
  }, [evaluationNodes, rootUniqueId, expandedRecords]);

  const toggleExpanded = useCallback((uniqueId: string) => {
    setExpandedRecords((expandedRecords) => {
      const copy = new Set(expandedRecords);
      if (copy.has(uniqueId)) {
        copy.delete(uniqueId);
      } else {
        copy.add(uniqueId);
      }
      return copy;
    });
  }, []);

  if (!isLegacyEvaluation) {
    return (
      <NewPolicyEvaluationTable
        assetKeyPath={assetKeyPath}
        evaluationId={evaluationId}
        flattenedRecords={flattened as FlattenedConditionEvaluation<NewEvaluationNodeFragment>[]}
        toggleExpanded={toggleExpanded}
        expandedRecords={expandedRecords}
      />
    );
  }

  if (flattened[0]?.evaluation.__typename === 'PartitionedAssetConditionEvaluationNode') {
    return (
      <PartitionedPolicyEvaluationTable
        flattenedRecords={
          flattened as FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[]
        }
        assetKeyPath={assetKeyPath}
        evaluationId={evaluationId}
        rootUniqueId={rootUniqueId}
        selectPartition={selectPartition}
        toggleExpanded={toggleExpanded}
        expandedRecords={expandedRecords}
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
      toggleExpanded={toggleExpanded}
      expandedRecords={expandedRecords}
    />
  );
};

const NewPolicyEvaluationTable = ({
  assetKeyPath,
  evaluationId,
  flattenedRecords,
  expandedRecords,
  toggleExpanded,
}: {
  assetKeyPath: string[] | null;
  evaluationId: string;
  expandedRecords: Set<string>;
  toggleExpanded: (id: string) => void;
  flattenedRecords: FlattenedConditionEvaluation<NewEvaluationNodeFragment>[];
}) => {
  const [hoveredKey, setHoveredKey] = useState<number | null>(null);
  const isPartitioned = !!flattenedRecords[0]?.evaluation.isPartitioned;
  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          {isPartitioned ? <th>Partitions evaluated</th> : null}
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
          const {userLabel, uniqueId, numTrue, numCandidates, expandedLabel} = evaluation;
          const anyCandidatePartitions = numCandidates === null || numCandidates > 0;
          const status =
            numTrue === 0 && !anyCandidatePartitions
              ? AssetConditionEvaluationStatus.SKIPPED
              : numTrue > 0
                ? AssetConditionEvaluationStatus.TRUE
                : AssetConditionEvaluationStatus.FALSE;

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
              onClick={() => {
                toggleExpanded(uniqueId);
              }}
            >
              <td style={{width: '70%'}}>
                <PolicyEvaluationCondition
                  icon={
                    status === AssetConditionEvaluationStatus.TRUE ? (
                      <Icon name="check_circle" color={Colors.accentGreen()} />
                    ) : (
                      <Icon name="cancel" color={Colors.accentGray()} />
                    )
                  }
                  label={
                    userLabel ? (
                      <EvaluationUserLabel userLabel={userLabel} expandedLabel={expandedLabel} />
                    ) : (
                      <EvaluationConditionalLabel segments={expandedLabel} />
                    )
                  }
                  skipped={status === AssetConditionEvaluationStatus.SKIPPED}
                  depth={depth}
                  type={type}
                  isExpanded={expandedRecords.has(uniqueId)}
                  hasChildren={evaluation.childUniqueIds.length > 0}
                />
              </td>
              {isPartitioned && assetKeyPath ? (
                <td style={{width: 0}}>
                  <Box
                    flex={{direction: 'row', alignItems: 'center', gap: 2}}
                    style={{width: FULL_SEGMENTS_WIDTH}}
                  >
                    <PartitionSegmentWithPopover
                      description={
                        userLabel ||
                        (numTrue === 1
                          ? '1 partition'
                          : `${numberFormatter.format(numTrue)} partitions`)
                      }
                      assetKeyPath={assetKeyPath}
                      evaluationId={evaluationId}
                      nodeUniqueId={evaluation.uniqueId}
                      numTrue={numTrue}
                    />
                  </Box>
                </td>
              ) : (
                <td>
                  <PolicyEvaluationStatusTag status={status} />
                </td>
              )}
              {isPartitioned ? <td>{numCandidates === null ? 'All' : numCandidates}</td> : null}
              <td>
                {startTimestamp && endTimestamp ? (
                  <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} showMsec />
                ) : (
                  '\u2014'
                )}
              </td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const UnpartitionedPolicyEvaluationTable = ({
  flattenedRecords,
  expandedRecords,
  toggleExpanded,
}: {
  expandedRecords: Set<string>;
  toggleExpanded: (id: string) => void;
  flattenedRecords:
    | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>[]
    | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>[];
}) => {
  const [hoveredKey, setHoveredKey] = useState<number | null>(null);
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
          const {description, status, uniqueId} = evaluation;
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
              onClick={() => {
                toggleExpanded(uniqueId);
              }}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={
                    <Icon
                      name={type === 'group' ? 'resource' : 'wysiwyg'}
                      color={Colors.accentPrimary()}
                    />
                  }
                  label={description}
                  skipped={status === AssetConditionEvaluationStatus.SKIPPED}
                  depth={depth}
                  type={type}
                  isExpanded={expandedRecords.has(uniqueId)}
                  hasChildren={evaluation.childUniqueIds.length > 0}
                />
              </td>
              <td>
                <PolicyEvaluationStatusTag status={status} />
              </td>
              {startTimestamp && endTimestamp ? (
                <td>
                  <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} showMsec />
                </td>
              ) : null}
              <td>
                {evaluation.metadataEntries?.length ? (
                  <ViewDetailsButton evaluation={evaluation} />
                ) : null}
              </td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const ViewDetailsButton = ({
  evaluation,
}: {
  evaluation: {metadataEntries: MetadataEntryFragment[]};
}) => {
  const [showDetails, setShowDetails] = useState(false);
  return (
    <>
      <Dialog
        title="Evaluation metadata"
        isOpen={showDetails}
        onClose={() => {
          setShowDetails(false);
        }}
      >
        <Box padding={8}>
          <AssetEventMetadataEntriesTable showDescriptions event={evaluation} repoAddress={null} />
        </Box>
        <DialogFooter>
          <Button onClick={() => setShowDetails(false)}>Done</Button>
        </DialogFooter>
      </Dialog>
      <ButtonLink
        onClick={() => {
          setShowDetails(true);
        }}
      >
        View details
      </ButtonLink>
    </>
  );
};

const FULL_SEGMENTS_WIDTH = 200;

export const PartitionedPolicyEvaluationTable = ({
  assetKeyPath,
  evaluationId,
  rootUniqueId,
  flattenedRecords,
  expandedRecords,
  toggleExpanded,
  selectPartition,
}: {
  assetKeyPath: string[] | null;
  evaluationId: string;
  rootUniqueId: string;
  flattenedRecords: FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[];
  expandedRecords: Set<string>;
  toggleExpanded: (id: string) => void;
  selectPartition: (partitionKey: string | null) => void;
}) => {
  const [hoveredKey, setHoveredKey] = useState<number | null>(null);
  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Partitions evaluated</th>
          <th>Result</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
          const {description, endTimestamp, startTimestamp, numCandidates, numTrue, uniqueId} =
            evaluation;

          return (
            <EvaluationRow
              key={id}
              $highlight={
                hoveredKey === id ? 'hovered' : parentId === hoveredKey ? 'highlighted' : 'none'
              }
              onMouseEnter={() => setHoveredKey(id)}
              onMouseLeave={() => setHoveredKey(null)}
              onClick={() => {
                toggleExpanded(uniqueId);
              }}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={
                    <Icon
                      name={type === 'group' ? 'resource' : 'wysiwyg'}
                      color={Colors.accentPrimary()}
                    />
                  }
                  label={description}
                  depth={depth}
                  type={type}
                  isExpanded={expandedRecords.has(evaluation.uniqueId)}
                  hasChildren={evaluation.childUniqueIds.length > 0}
                />
              </td>
              <td>
                {numCandidates ? (
                  <>{numberFormatter.format(numCandidates)}</>
                ) : (
                  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                    All
                    <Tooltip content="Evaluated against all partitions that existed at the time of evaluation">
                      <Icon name="info" />
                    </Tooltip>
                  </Box>
                )}
              </td>
              <td style={{width: 0}}>
                {assetKeyPath ? (
                  <Box
                    flex={{direction: 'row', alignItems: 'center', gap: 2}}
                    style={{width: FULL_SEGMENTS_WIDTH}}
                  >
                    <PartitionSegmentWithPopover
                      description={description}
                      assetKeyPath={assetKeyPath}
                      numTrue={numTrue}
                      evaluationId={evaluationId}
                      nodeUniqueId={rootUniqueId}
                      selectPartition={selectPartition}
                    />
                  </Box>
                ) : null}
              </td>
              <td>
                <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} showMsec />
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
    padding: 4px 16px;
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
  cursor: pointer;
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
