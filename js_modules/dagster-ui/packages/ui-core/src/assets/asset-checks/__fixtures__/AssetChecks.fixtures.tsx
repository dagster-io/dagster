import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  buildAssetCheck,
  buildAssetCheckEvaluation,
  buildAssetCheckEvaluationTargetMaterializationData,
  buildAssetCheckExecution,
  buildAssetKey,
  buildIntMetadataEntry,
  buildTable,
  buildTableColumn,
  buildTableMetadataEntry,
  buildTableSchema,
} from '../../../graphql/types';

export const testAssetKey = {path: ['test']};
export const testLatestMaterializationTimeStamp = Date.now();
export const testLatestMaterializationRunId = 'abc123d6';

export const TestAssetCheck = buildAssetCheck({
  assetKey: buildAssetKey(testAssetKey),
  name: 'Test check',
  description: 'Test description',
  executions: [
    buildAssetCheckExecution({
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
    buildAssetCheckExecution({
      evaluation: buildAssetCheckEvaluation({
        targetMaterialization: buildAssetCheckEvaluationTargetMaterializationData({
          timestamp: testLatestMaterializationTimeStamp,
          runId: testLatestMaterializationRunId,
        }),
        metadataEntries: [
          buildTableMetadataEntry({
            table: buildTable({
              records: [JSON.stringify({test: 'hi'})],
              schema: buildTableSchema({
                columns: [
                  buildTableColumn({
                    name: 'test',
                    description: 'A test column description',
                  }),
                ],
              }),
            }),
          }),
        ],
      }),
    }),
  ],
});

export const TestAssetCheckWarning = buildAssetCheck({
  assetKey: buildAssetKey(testAssetKey),
  name: 'Test check warning',
  description: 'Test description',

  executions: [
    buildAssetCheckExecution({
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
    buildAssetCheckExecution({
      evaluation: buildAssetCheckEvaluation({
        targetMaterialization: buildAssetCheckEvaluationTargetMaterializationData({
          timestamp: testLatestMaterializationTimeStamp,
          runId: testLatestMaterializationRunId,
        }),
        metadataEntries: [
          buildTableMetadataEntry({
            table: buildTable({
              records: [JSON.stringify({test: 'hi'})],
              schema: buildTableSchema({
                columns: [
                  buildTableColumn({
                    name: 'test',
                    description: 'A test column description',
                  }),
                ],
              }),
            }),
          }),
        ],
      }),
    }),
  ],
});

export const TestAssetCheckNoExecutions = buildAssetCheck({
  assetKey: buildAssetKey(testAssetKey),
  name: 'Test check',
  description: 'Test description',
  executions: [],
});
