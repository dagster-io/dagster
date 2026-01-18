import {useMemo} from 'react';

import {
  GET_ASSET_EVALUATION_DETAILS_QUERY,
  GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY,
} from './GetEvaluationsQuery';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {tokenForEntityKey} from './flattenEvaluations';
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
import {EntityKey} from '../../graphql/types';
import {AssetKey} from '../types';
import {EvaluationHistoryStackItem} from './types';

interface EvaluationDetailDialogContentsProps {
  evaluation: AssetConditionEvaluationRecordFragment;
  entityKey: EntityKey;
  selectedPartition: string | null;
  setSelectedPartition: (partition: string | null) => void;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}

export const QueryfulEvaluationDetailTable = ({
  evaluation,
  entityKey,
  selectedPartition,
  setSelectedPartition,
  pushHistory,
}: EvaluationDetailDialogContentsProps) => {
  const assetKeyPath =
    entityKey.__typename === 'AssetKey' ? entityKey.path : entityKey.assetKey.path;
  const partitionQuery = useQuery<
    GetEvaluationsSpecificPartitionQuery,
    GetEvaluationsSpecificPartitionQueryVariables
  >(GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY, {
    variables: {
      assetKey: {path: assetKeyPath},
      evaluationId: evaluation.evaluationId,
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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

  // Fetch the latest evaluation details for all asset keys in the evaluation tree.
  // This is used to reference deps, to navigate asset lineage.  This will not traverse lineage for
  // upstream asset checks.  To do that, we would need to batch fetch the last evaluations by entity
  // key instead of by asset key.
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
    const evaluationsByAssetKey: {[entityKeyToken: string]: AssetLastEvaluationFragment} = {};
    detailsData?.assetNodes.forEach((node) => {
      if (node.lastAutoMaterializationEvaluationRecord) {
        evaluationsByAssetKey[tokenForEntityKey(node.assetKey)] =
          node.lastAutoMaterializationEvaluationRecord;
      }
    });
    return evaluationsByAssetKey;
  }, [detailsData]);
  return (
    <PolicyEvaluationTable
      assetKeyPath={assetKeyPath}
      assetCheckName={entityKey.__typename === 'AssetCheckhandle' ? entityKey.name : undefined}
      evaluationId={evaluation.evaluationId}
      lastEvaluationsByEntityKey={lastEvaluationsByAssetKey}
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
      pushHistory={pushHistory}
    />
  );
};
