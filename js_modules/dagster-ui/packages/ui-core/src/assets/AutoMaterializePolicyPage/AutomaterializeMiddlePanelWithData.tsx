import {gql, useQuery} from '@apollo/client';
import {
  BaseTag,
  Box,
  Colors,
  Icon,
  MenuItem,
  MiddleTruncate,
  Popover,
  Subheading,
  Subtitle2,
  Tag,
  TagSelectorContainer,
  TagSelectorDefaultTagTooltipStyle,
  TagSelectorWithSearch,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import styled from 'styled-components';

import {StatusDot} from './AutomaterializeLeftPanel';
import {AutomaterializeRunsTable} from './AutomaterializeRunsTable';
import {PartitionSubsetList} from './PartitionSegmentWithPopover';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {
  FullPartitionsQuery,
  FullPartitionsQueryVariables,
} from './types/AutomaterializeMiddlePanelWithData.types';
import {
  AssetConditionEvaluationRecordFragment,
  GetEvaluationsSpecificPartitionQuery,
} from './types/GetEvaluationsQuery.types';
import {formatElapsedTimeWithMsec} from '../../app/Util';
import {Timestamp} from '../../app/time/Timestamp';
import {DimensionPartitionKeys} from '../../graphql/types';
import {useBlockTraceOnQueryResult} from '../../performance/TraceContext';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

const emptyArray: any[] = [];

interface Props {
  definition?: AssetViewDefinitionNodeFragment | null;
  selectedEvaluation?: AssetConditionEvaluationRecordFragment;
  selectPartition: (partitionKey: string | null) => void;
  specificPartitionData?: GetEvaluationsSpecificPartitionQuery;
  selectedPartition: string | null;
}

export const AutomaterializeMiddlePanelWithData = ({
  selectedEvaluation,
  definition,
  selectPartition,
  specificPartitionData,
  selectedPartition,
}: Props) => {
  const evaluation = selectedEvaluation?.evaluation;
  const rootEvaluationNode = useMemo(
    () => evaluation?.evaluationNodes.find((node) => node.uniqueId === evaluation.rootUniqueId),
    [evaluation],
  );
  const partitionDefinition = definition?.partitionDefinition;
  const numRequested = selectedEvaluation?.numRequested;

  const statusTag = useMemo(() => {
    const trueSubset =
      rootEvaluationNode?.__typename === 'PartitionedAssetConditionEvaluationNode'
        ? rootEvaluationNode.trueSubset
        : null;

    if (numRequested) {
      if (partitionDefinition && trueSubset) {
        return (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <Popover
              interactionKind="hover"
              placement="bottom"
              hoverOpenDelay={50}
              hoverCloseDelay={50}
              content={
                <PartitionSubsetList
                  description="Requested assets"
                  subset={trueSubset}
                  selectPartition={selectPartition}
                />
              }
            >
              <Tag intent="success">
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  <StatusDot $color={Colors.accentGreen()} $size={8} />
                  {numRequested} requested
                </Box>
              </Tag>
            </Popover>
            {numRequested === 1 ? (
              <Tag icon="partition">{trueSubset.subsetValue.partitionKeys![0]}</Tag>
            ) : null}
          </Box>
        );
      }

      return (
        <Tag intent="success">
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <StatusDot $color={Colors.accentGreen()} />
            Requested
          </Box>
        </Tag>
      );
    }

    return (
      <Tag>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <StatusDot $color={Colors.accentGray()} />
          Not requested
        </Box>
      </Tag>
    );
  }, [partitionDefinition, selectPartition, numRequested, rootEvaluationNode]);

  const fullPartitionsQueryResult = useQuery<FullPartitionsQuery, FullPartitionsQueryVariables>(
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
  useBlockTraceOnQueryResult(fullPartitionsQueryResult, 'FullPartitionsQuery', {
    skip: !definition?.assetKey,
  });

  const {data} = fullPartitionsQueryResult;

  let partitionKeys: DimensionPartitionKeys[] = emptyArray;
  if (data?.assetNodeOrError.__typename === 'AssetNode') {
    partitionKeys = data.assetNodeOrError.partitionKeysByDimension;
  }

  const allPartitions = useMemo(() => {
    if (partitionKeys.length === 1) {
      return partitionKeys[0]!.partitionKeys;
    }

    if (partitionKeys.length === 2) {
      const firstSet = partitionKeys[0]!.partitionKeys;
      const secondSet = partitionKeys[1]!.partitionKeys;
      return firstSet.flatMap((key1) => secondSet.map((key2) => `${key1}|${key2}`));
    }

    if (partitionKeys.length > 2) {
      throw new Error('Only 2 dimensions are supported');
    }

    return [];
  }, [partitionKeys]);

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        style={{flex: '0 0 48px'}}
        padding={{horizontal: 16}}
        border="bottom"
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Result</Subheading>
      </Box>
      {selectedEvaluation ? (
        <Box padding={{horizontal: 24, vertical: 12}}>
          <Box border="bottom" padding={{vertical: 12}} margin={{bottom: 12}}>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24}}>
              <Box flex={{direction: 'column', gap: 5}}>
                <Subtitle2>Evaluation result</Subtitle2>
                <div>{statusTag}</div>
              </Box>
              {selectedEvaluation?.timestamp ? (
                <Box flex={{direction: 'column', gap: 5}}>
                  <Subtitle2>Timestamp</Subtitle2>
                  <Timestamp timestamp={{unix: selectedEvaluation?.timestamp}} />
                </Box>
              ) : null}
              <Box flex={{direction: 'column', gap: 5}}>
                <Subtitle2>Duration</Subtitle2>
                <div>
                  {selectedEvaluation?.startTimestamp && selectedEvaluation?.endTimestamp
                    ? formatElapsedTimeWithMsec(
                        (selectedEvaluation.endTimestamp - selectedEvaluation.startTimestamp) *
                          1000,
                      )
                    : '\u2013'}
                </div>
              </Box>
            </div>
          </Box>
          <Box border="bottom" padding={{vertical: 12}} margin={{vertical: 12}}>
            <Subtitle2>Runs launched ({selectedEvaluation.runIds.length})</Subtitle2>
          </Box>
          <AutomaterializeRunsTable runIds={selectedEvaluation.runIds} />
          <Box border="bottom" padding={{vertical: 12}}>
            <Subtitle2>Policy evaluation</Subtitle2>
          </Box>
          {definition?.partitionDefinition && selectedEvaluation.isLegacy ? (
            <Box padding={{vertical: 12}} flex={{justifyContent: 'flex-end'}}>
              <TagSelectorWrapper>
                <TagSelectorWithSearch
                  closeOnSelect
                  placeholder="Select a partition to view its result"
                  allTags={allPartitions}
                  selectedTags={selectedPartition ? [selectedPartition] : []}
                  setSelectedTags={(tags) => {
                    selectPartition(tags[tags.length - 1] || null);
                  }}
                  renderDropdownItem={(tag, props) => (
                    <MenuItem text={tag} onClick={props.toggle} />
                  )}
                  renderDropdown={(dropdown) => (
                    <Box padding={{top: 8, horizontal: 4}} style={{width: '370px'}}>
                      {dropdown}
                    </Box>
                  )}
                  renderTag={(tag, tagProps) => (
                    <BaseTag
                      key={tag}
                      textColor={Colors.textLight()}
                      fillColor={Colors.backgroundGray()}
                      icon={<Icon name="partition" color={Colors.accentGray()} />}
                      label={
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr auto',
                            gap: 4,
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            maxWidth: '120px',
                          }}
                          data-tooltip={tag}
                          data-tooltip-style={TagSelectorDefaultTagTooltipStyle}
                        >
                          <MiddleTruncate text={tag} />
                          <Box style={{cursor: 'pointer'}} onClick={tagProps.remove}>
                            <Icon name="close" />
                          </Box>
                        </div>
                      }
                    />
                  )}
                  usePortal={false}
                />
                <SearchIconWrapper>
                  <Icon name="search" />
                </SearchIconWrapper>
              </TagSelectorWrapper>
            </Box>
          ) : null}
          <PolicyEvaluationTable
            evaluationNodes={
              !selectedEvaluation.isLegacy
                ? selectedEvaluation.evaluationNodes
                : selectedPartition && specificPartitionData?.assetConditionEvaluationForPartition
                ? specificPartitionData.assetConditionEvaluationForPartition.evaluationNodes
                : selectedEvaluation.evaluation.evaluationNodes
            }
            isLegacyEvaluation={selectedEvaluation.isLegacy}
            rootUniqueId={selectedEvaluation.evaluation.rootUniqueId}
            selectPartition={selectPartition}
          />
        </Box>
      ) : null}
    </Box>
  );
};

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

const TagSelectorWrapper = styled.div`
  position: relative;

  ${TagSelectorContainer} {
    width: 370px;
    padding-left: 32px;
    height: 36px;
  }
`;

const SearchIconWrapper = styled.div`
  position: absolute;
  left: 12px;
  top: 0px;
  bottom: 0px;
  pointer-events: none;
  display: flex;
  align-items: center;
`;
