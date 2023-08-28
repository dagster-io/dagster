import {
  buildAssetCheck,
  buildAssetCheckEvaluation,
  buildAssetCheckEvaluationTargetMaterializationData,
  buildAssetCheckExecution,
  buildAssetKey,
  buildBoolMetadataEntry,
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
        metadataEntries: [buildBoolMetadataEntry({})],
      }),
      runId: testLatestMaterializationRunId,
    }),
    buildAssetCheckExecution({
      evaluation: buildAssetCheckEvaluation({
        targetMaterialization: buildAssetCheckEvaluationTargetMaterializationData({
          timestamp: testLatestMaterializationTimeStamp,
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
