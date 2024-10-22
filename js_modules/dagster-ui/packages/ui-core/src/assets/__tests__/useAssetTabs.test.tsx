import {renderHook} from '@testing-library/react';

import {
  AutoMaterializeDecisionType,
  buildAssetKey,
  buildAssetNode,
  buildAutoMaterializePolicy,
  buildAutoMaterializeRule,
  buildCompositeConfigType,
  buildConfigTypeField,
  buildDimensionPartitionKeys,
  buildPartitionDefinition,
  buildRegularConfigType,
  buildRegularDagsterType,
  buildRepository,
  buildRepositoryLocation,
} from '../../graphql/types';
import {useAssetTabs} from '../AssetTabs';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

const autoMaterializePolicy = buildAutoMaterializePolicy({
  rules: [
    buildAutoMaterializeRule({
      decisionType: AutoMaterializeDecisionType.MATERIALIZE,
      description: 'Rule 1',
    }),
    buildAutoMaterializeRule({
      decisionType: AutoMaterializeDecisionType.SKIP,
      description: 'Skip Rule 1',
    }),
  ],
});

describe('buildAssetTabs', () => {
  const definitionWithPartition: AssetViewDefinitionNodeFragment = buildAssetNode({
    id: 'dagster_test.toys.repo.auto_materialize_repo_2.["eager_downstream_3_partitioned"]',
    groupName: 'default',
    partitionDefinition: buildPartitionDefinition({
      description: 'Daily, starting 2023-02-01 UTC.',
    }),
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'default',
      }),
    ],
    repository: buildRepository({
      id: 'cbff94a5bb24f8af0414f4041c450c02725a6ee6',
      name: 'auto_materialize_repo_2',
      location: buildRepositoryLocation({
        id: 'dagster_test.toys.repo',
        name: 'dagster_test.toys.repo',
      }),
    }),
    targetingInstigators: [],
    opNames: ['eager_downstream_3_partitioned'],
    jobNames: ['__ASSET_JOB_0'],
    autoMaterializePolicy,
    hasMaterializePermission: true,
    isPartitioned: true,
    isObservable: false,
    isExecutable: true,
    isMaterializable: true,
    assetKey: buildAssetKey({
      path: ['eager_downstream_3_partitioned'],
    }),
    type: buildRegularDagsterType({
      key: 'Any',
      name: 'Any',
      displayName: 'Any',
      isNullable: false,
      isList: false,
      isBuiltin: true,
      isNothing: false,
      inputSchemaType: buildCompositeConfigType({
        key: 'Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4',
        isSelector: true,
        typeParamKeys: [],
        fields: [
          buildConfigTypeField({
            name: 'json',
            isRequired: true,
            configTypeKey: 'Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2',
          }),
          buildConfigTypeField({
            name: 'pickle',
            isRequired: true,
            configTypeKey: 'Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2',
          }),
          buildConfigTypeField({
            name: 'value',
            isRequired: true,
            configTypeKey: 'Any',
          }),
        ],
        recursiveConfigTypes: [
          buildCompositeConfigType({
            key: 'Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2',
            isSelector: false,
            fields: [
              buildConfigTypeField({
                name: 'path',
                isRequired: true,
                configTypeKey: 'String',
              }),
            ],
          }),
        ],
      }),
    }),
  });

  // Copied from browser
  const definitionWithoutPartition = buildAssetNode({
    id: 'dagster_test.toys.repo.auto_materialize_repo_1.["lazy_downstream_1"]',
    groupName: 'default',
    partitionDefinition: null,
    partitionKeysByDimension: [],
    repository: buildRepository({
      id: '4d9fd77c222a797eb8427fcbe1968799ebc24de8',
      name: 'auto_materialize_repo_1',
      location: buildRepositoryLocation({
        id: 'dagster_test.toys.repo',
        name: 'dagster_test.toys.repo',
      }),
    }),
    description: null,
    graphName: null,
    targetingInstigators: [],
    opNames: ['lazy_downstream_1'],
    opVersion: null,
    jobNames: ['__ASSET_JOB_0'],
    autoMaterializePolicy,
    backfillPolicy: null,
    freshnessPolicy: null,
    requiredResources: [],
    configField: buildConfigTypeField({
      name: 'config',
      isRequired: false,
      configType: buildRegularConfigType({
        givenName: 'Any',
        key: 'Any',
        description: null,
        isSelector: false,
        typeParamKeys: [],
        recursiveConfigTypes: [],
      }),
    }),
    hasMaterializePermission: true,
    computeKind: null,
    isPartitioned: false,
    isObservable: false,
    isExecutable: true,
    isMaterializable: true,
    assetKey: buildAssetKey({
      path: ['lazy_downstream_1'],
    }),
    metadataEntries: [],
    owners: [],
    type: buildRegularDagsterType({
      key: 'Any',
      name: 'Any',
      displayName: 'Any',
      description: null,
      isNullable: false,
      isList: false,
      isBuiltin: true,
      isNothing: false,
      metadataEntries: [],
      inputSchemaType: buildCompositeConfigType({
        key: 'Selector.f2fe6dfdc60a1947a8f8e7cd377a012b47065bc4',
        description: null,
        isSelector: true,
        typeParamKeys: [],
        fields: [
          buildConfigTypeField({
            name: 'json',
            description: null,
            isRequired: true,
            configTypeKey: 'Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2',
            defaultValueAsJson: null,
          }),
          buildConfigTypeField({
            name: 'pickle',
            description: null,
            isRequired: true,
            configTypeKey: 'Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2',
            defaultValueAsJson: null,
          }),
          buildConfigTypeField({
            name: 'value',
            description: null,
            isRequired: true,
            configTypeKey: 'Any',
            defaultValueAsJson: null,
          }),
        ],
        recursiveConfigTypes: [
          buildCompositeConfigType({
            key: 'Shape.4b53b73df342381d0d05c5f36183dc99cb9676e2',
            description: null,
            isSelector: false,
            typeParamKeys: [],
            fields: [
              buildConfigTypeField({
                name: 'path',
                description: null,
                isRequired: true,
                configTypeKey: 'String',
                defaultValueAsJson: null,
              }),
            ],
          }),
          buildRegularConfigType({
            givenName: 'String',
            key: 'String',
            description: '',
            isSelector: false,
            typeParamKeys: [],
          }),
          buildRegularConfigType({
            givenName: 'Any',
            key: 'Any',
            description: null,
            isSelector: false,
            typeParamKeys: [],
          }),
        ],
      }),
      outputSchemaType: null,
      innerTypes: [],
    }),
  });
  const params = {};

  it('shows all tabs', () => {
    const hookResult = renderHook(() =>
      useAssetTabs({definition: definitionWithPartition, params}),
    );
    const tabKeys = hookResult.result.current.map(({id}) => id);
    expect(tabKeys).toEqual([
      'overview',
      'partitions',
      'events',
      'checks',
      'lineage',
      'automation',
    ]);
  });

  it('hides auto-materialize tab if no auto-materialize policy', () => {
    const hookResult = renderHook(() =>
      useAssetTabs({
        definition: {...definitionWithPartition, automationCondition: null},
        params,
      }),
    );
    const tabKeys = hookResult.result.current.map(({id}) => id);
    expect(tabKeys).toEqual(['overview', 'partitions', 'events', 'checks', 'lineage']);
  });

  it('hides partitions tab if no partitions', () => {
    const hookResult = renderHook(() =>
      useAssetTabs({
        definition: definitionWithoutPartition,
        params,
      }),
    );
    const tabKeys = hookResult.result.current.map(({id}) => id);
    expect(tabKeys).toEqual(['overview', 'events', 'checks', 'lineage', 'automation']);
  });

  it('hides partitions and auto-materialize tabs if no partitions or auto-materializing', () => {
    const hookResult = renderHook(() =>
      useAssetTabs({
        definition: {...definitionWithoutPartition, automationCondition: null},
        params,
      }),
    );
    const tabKeys = hookResult.result.current.map(({id}) => id);
    expect(tabKeys).toEqual(['overview', 'events', 'checks', 'lineage']);
  });
});
