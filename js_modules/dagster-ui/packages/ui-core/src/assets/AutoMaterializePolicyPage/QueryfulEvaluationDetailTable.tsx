import {GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY} from './GetEvaluationsQuery';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {useQuery} from '../../apollo-client';
import {
  AssetConditionEvaluationRecordFragment,
  GetEvaluationsSpecificPartitionQuery,
  GetEvaluationsSpecificPartitionQueryVariables,
} from './types/GetEvaluationsQuery.types';

interface EvaluationDetailDialogContentsProps {
  evaluation: AssetConditionEvaluationRecordFragment;
  assetKeyPath: string[];
  selectedPartition: string | null;
  setSelectedPartition: (partition: string | null) => void;
}

export const QueryfulEvaluationDetailTable = ({
  evaluation,
  assetKeyPath,
  selectedPartition,
  setSelectedPartition,
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

  const {data: specificPartitionData} = partitionQuery;

  return (
    <PolicyEvaluationTable
      assetKeyPath={assetKeyPath}
      evaluationId={evaluation.evaluationId}
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
    />
  );
};
