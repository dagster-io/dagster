import {useMemo} from 'react';

import {
  GET_ASSET_EVALUATION_DETAILS_QUERY,
  GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY,
} from './GetEvaluationsQuery';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {useQuery} from '../../apollo-client';
import {
  AssetConditionEvaluationRecordFragment,
  AssetLastEvaluationFragment,
  GetAssetEvaluationDetailsQuery,
  GetAssetEvaluationDetailsQueryVariables,
  GetEvaluationsSpecificPartitionQuery,
  GetEvaluationsSpecificPartitionQueryVariables,
} from './types/GetEvaluationsQuery.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetKey} from '../types';

interface EvaluationDetailDialogContentsProps {
  evaluation: AssetConditionEvaluationRecordFragment;
  assetKeyPath: string[];
  selectedPartition: string | null;
  setSelectedPartition: (partition: string | null) => void;
  onEntityChange?: (args: {
    assetKeyPath: string[];
    assetCheckName: string | undefined;
    evaluationId?: string;
  }) => void;
}

export const QueryfulEvaluationDetailTable = ({
  evaluation,
  assetKeyPath,
  selectedPartition,
  setSelectedPartition,
  onEntityChange,
}: EvaluationDetailDialogContentsProps) => {
  const partitionQuery = useQuery<
    GetEvaluationsSpecificPartitionQuery,
    GetEvaluationsSpecificPartitionQueryVariables
  >(GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY, {
    variables: {
      assetKey: {path: assetKeyPath},
      evaluationId: evaluation.evaluationId,
      partition: selectedPartition!,
    },
    skip: !selectedPartition || !evaluation.isLegacy,
  });

  const allAssetKeys = useMemo(() => {
    const tokens = new Set();
    const assetKeys: AssetKey[] = [];
    evaluation.evaluationNodes.forEach((node) => {
      if (node.entityKey.__typename !== 'AssetKey') {
        return;
      }
      const token = tokenForAssetKey(node.entityKey);
      if (tokens.has(token)) {
        return;
      }
      tokens.add(token);
      assetKeys.push(node.entityKey);
    });
    return assetKeys;
  }, [evaluation]);

  const detailsQuery = useQuery<
    GetAssetEvaluationDetailsQuery,
    GetAssetEvaluationDetailsQueryVariables
  >(GET_ASSET_EVALUATION_DETAILS_QUERY, {
    variables: {
      assetKeys: allAssetKeys.map((key) => ({path: key.path})),
      asOfEvaluationId: evaluation.evaluationId,
    },
  });

  const entityKeys = evaluation.evaluationNodes.map((node) => node.entityKey);
  const allAssetKeyTokens = new Set();
  entityKeys.forEach((key) => {
    if (key.__typename === 'AssetKey') {
      allAssetKeyTokens.add(tokenForAssetKey(key));
    }
  });
  const {data: specificPartitionData} = partitionQuery;
  const {data: detailsData} = detailsQuery;
  const lastEvaluationsByAssetKey = useMemo(() => {
    const evaluationsByAssetKey: {[assetKeyToken: string]: AssetLastEvaluationFragment} = {};
    detailsData?.assetNodes.forEach((node) => {
      if (node.lastAutoMaterializationEvaluationRecord) {
        evaluationsByAssetKey[tokenForAssetKey(node.assetKey)] =
          node.lastAutoMaterializationEvaluationRecord;
      }
    });
    return evaluationsByAssetKey;
  }, [detailsData]);
  return (
    <PolicyEvaluationTable
      assetKeyPath={assetKeyPath}
      evaluationId={evaluation.evaluationId}
      lastEvaluationsByAssetKey={lastEvaluationsByAssetKey}
      evaluationNodes={
        !evaluation.isLegacy
          ? evaluation.evaluationNodes
          : selectedPartition && specificPartitionData?.assetConditionEvaluationForPartition
            ? specificPartitionData.assetConditionEvaluationForPartition.evaluationNodes
            : evaluation.evaluation.evaluationNodes
      }
      isLegacyEvaluation={evaluation.isLegacy}
      rootUniqueId={evaluation.evaluation.rootUniqueId}
      selectPartition={setSelectedPartition}
      onEntityChange={onEntityChange}
    />
  );
};
