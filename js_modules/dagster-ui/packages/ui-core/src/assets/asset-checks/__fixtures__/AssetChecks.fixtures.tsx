import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  buildAssetCheck,
  buildAssetCheckEvaluation,
  buildAssetCheckEvaluationTargetMaterializationData,
  buildAssetCheckExecution,
  buildAssetKey,
  buildIntMetadataEntry,
} from '../../../graphql/types';

export const testAssetKey = {path: ['test']};
export const testLatestMaterializationTimeStamp = Date.now();
export const testLatestMaterializationRunId = 'abc123d6';

export const TestAssetCheck = buildAssetCheck({
  assetKey: buildAssetKey(testAssetKey),
  name: 'Test check',
  description: 'Test description',
  executionForLatestMaterialization: buildAssetCheckExecution({
    id: '1234',
    evaluation: buildAssetCheckEvaluation({
      targetMaterialization: buildAssetCheckEvaluationTargetMaterializationData({
        timestamp: testLatestMaterializationTimeStamp,
        runId: testLatestMaterializationRunId,
      }),
      metadataEntries: [buildIntMetadataEntry({})],
      severity: AssetCheckSeverity.ERROR,
    }),
    runId: testLatestMaterializationRunId,
    status: AssetCheckExecutionResolvedStatus.FAILED,
  }),
});

export const TestAssetCheckWarning = buildAssetCheck({
  assetKey: buildAssetKey(testAssetKey),
  name: 'Test check warning',
  description: 'Test description',
  executionForLatestMaterialization: buildAssetCheckExecution({
    id: '5678',
    evaluation: buildAssetCheckEvaluation({
      targetMaterialization: buildAssetCheckEvaluationTargetMaterializationData({
        timestamp: testLatestMaterializationTimeStamp,
        runId: testLatestMaterializationRunId,
      }),
      metadataEntries: [buildIntMetadataEntry({})],
      severity: AssetCheckSeverity.WARN,
    }),
    runId: testLatestMaterializationRunId,
    status: AssetCheckExecutionResolvedStatus.FAILED,
  }),
});
