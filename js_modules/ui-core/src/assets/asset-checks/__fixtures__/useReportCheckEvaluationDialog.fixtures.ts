import {MockedResponse} from '@apollo/client/testing';

import {
  buildAssetKey,
  buildAssetNode,
  buildDimensionDefinitionType,
  buildMutation,
  buildPartitionDefinition,
  buildReportAssetCheckEvaluationsSuccess,
} from '../../../graphql/builders';
import {PartitionDefinitionType} from '../../../graphql/types';
import {buildMutationMock, buildQueryMock} from '../../../testing/mocking';
import {
  REPORT_CHECK_EVALUATION_MUTATION,
  REPORT_EVENT_PARTITION_DEFINITION_QUERY,
} from '../../ReportEventsQueries';
import {ONE_DIMENSIONAL_ASSET} from '../../__fixtures__/PartitionHealth.fixtures';
import {
  ReportCheckEvaluationMutation,
  ReportCheckEvaluationMutationVariables,
  ReportEventPartitionDefinitionQuery,
  ReportEventPartitionDefinitionQueryVariables,
} from '../../types/ReportEventsQueries.types';
import {
  PartitionHealthQuery,
  PartitionHealthQueryVariables,
} from '../../types/usePartitionHealthData.types';
import {PARTITION_HEALTH_QUERY} from '../../usePartitionHealthData';

export const testCheck = {
  name: 'my_freshness_check',
  assetKey: {path: ['my_asset']},
  isPartitioned: false,
  repoAddress: {location: 'my_location', name: 'my_repo'},
  hasReportRunlessAssetEventPermission: true,
};

export const testCheckPartitioned = {
  name: 'my_freshness_check',
  assetKey: {path: ['my_partitioned_asset']},
  isPartitioned: true,
  repoAddress: {location: 'my_location', name: 'my_repo'},
  hasReportRunlessAssetEventPermission: true,
};

// -- Unpartitioned mocks --

export const buildReportCheckPartitionDefinitionQueryMock = () =>
  buildQueryMock<ReportEventPartitionDefinitionQuery, ReportEventPartitionDefinitionQueryVariables>(
    {
      query: REPORT_EVENT_PARTITION_DEFINITION_QUERY,
      variables: {assetKey: {path: testCheck.assetKey.path}},
      data: {
        assetNodeOrError: buildAssetNode({partitionDefinition: null}),
      },
    },
  );

export const buildReportCheckPassedMutationMock = () =>
  buildMutationMock<ReportCheckEvaluationMutation, ReportCheckEvaluationMutationVariables>({
    query: REPORT_CHECK_EVALUATION_MUTATION,
    variables: {
      eventParams: {
        assetKey: {path: testCheck.assetKey.path},
        checkName: testCheck.name,
        passed: true,
      },
    },
    data: {
      reportAssetCheckEvaluations: buildReportAssetCheckEvaluationsSuccess({
        assetKey: buildAssetKey({path: testCheck.assetKey.path}),
      }),
    },
  });

// -- Partitioned mocks --

export const buildReportCheckPartitionedPartitionDefinitionQueryMock = () =>
  buildQueryMock<ReportEventPartitionDefinitionQuery, ReportEventPartitionDefinitionQueryVariables>(
    {
      query: REPORT_EVENT_PARTITION_DEFINITION_QUERY,
      variables: {assetKey: {path: testCheckPartitioned.assetKey.path}},
      data: {
        assetNodeOrError: buildAssetNode({
          partitionDefinition: buildPartitionDefinition({
            type: PartitionDefinitionType.TIME_WINDOW,
            name: null,
            dimensionTypes: [
              buildDimensionDefinitionType({
                type: PartitionDefinitionType.TIME_WINDOW,
                name: 'default',
                dynamicPartitionsDefinitionName: null,
              }),
            ],
          }),
        }),
      },
    },
  );

export const buildReportCheckPartitionHealthQueryMock = () =>
  buildQueryMock<PartitionHealthQuery, PartitionHealthQueryVariables>({
    query: PARTITION_HEALTH_QUERY,
    variables: {assetKey: {path: testCheckPartitioned.assetKey.path}},
    data: ONE_DIMENSIONAL_ASSET,
  });

// Flexible mutation mock — matches any variables via variableMatcher, suitable for stories
// where the exact partition keys selected are unknown ahead of time. newData is called after
// the match succeeds, so variableMatcher: () => true is required to bypass variable equality.
export const buildReportCheckAnyMutationMock = (): MockedResponse => ({
  request: {query: REPORT_CHECK_EVALUATION_MUTATION},
  variableMatcher: () => true,
  newData: () => ({
    data: buildMutation({
      reportAssetCheckEvaluations: buildReportAssetCheckEvaluationsSuccess(),
    }),
  }),
});
