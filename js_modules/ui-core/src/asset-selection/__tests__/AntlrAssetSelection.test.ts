/* eslint-disable jest/expect-expect */
import {AssetGraphQueryItem} from '../../asset-graph/types';
import {
  buildAssetKey,
  buildAssetNode,
  buildDefinitionTag,
  buildDimensionDefinitionType,
  buildPartitionDefinition,
  buildRepository,
  buildRepositoryLocation,
  buildUserAssetOwner,
} from '../../graphql/builders';
import {PartitionDefinitionType} from '../../graphql/types';
import {parseAssetSelectionQuery} from '../parseAssetSelectionQuery';
import {SupplementaryInformation} from '../types';
import {getSupplementaryDataKey} from '../util';

const TEST_GRAPH: AssetGraphQueryItem[] = [
  // Top Layer
  {
    name: 'A',
    node: buildAssetNode({
      tags: [buildDefinitionTag({key: 'foo', value: 'bar'})],
      owners: [buildUserAssetOwner({email: 'owner@owner.com'})],
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
  },
  // Second Layer
  {
    name: 'B',
    node: buildAssetNode({
      tags: [buildDefinitionTag({key: 'foo', value: ''})],
      kinds: ['python', 'snowflake'],
    }),
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },
  {
    name: 'B2',
    node: buildAssetNode({
      repository: buildRepository({
        name: '',
        location: buildRepositoryLocation({name: ''}),
      }),
      owners: [],
      tags: [],
      groupName: undefined,
      kinds: [],
    }),
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },
  // Third Layer
  {
    name: 'C',
    node: buildAssetNode({
      groupName: 'my_group',
      repository: buildRepository({
        name: 'repo',
        location: buildRepositoryLocation({name: 'my_location'}),
      }),
    }),
    inputs: [{dependsOn: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
    outputs: [{dependedBy: []}],
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseAssetSelectionQuery(TEST_GRAPH, query);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(result.all.map((asset) => asset.name))).toEqual(new Set(expectedNames));
  expect(result.all.length).toBe(expectedNames.length);
}

describe('parseAssetSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'A')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'key:A key:B')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'not')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'and')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'key:A and')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'sinks')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'notafunction()')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'tag:foo=')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'owner')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toBeInstanceOf(Error);
    });
  });

  describe('valid queries', () => {
    it('should parse star query', () => {
      assertQueryResult('*', ['A', 'B', 'B2', 'C']);
    });

    it('should parse key query', () => {
      assertQueryResult('key:A', ['A']);
    });

    it('should parse and query', () => {
      assertQueryResult('key:A and key:B', []);
      assertQueryResult('key:A and key:B and key:C', []);
    });

    it('should parse or query', () => {
      assertQueryResult('key:A or key:B', ['A', 'B']);
      assertQueryResult('key:A or key:B or key:C', ['A', 'B', 'C']);
      assertQueryResult('(key:A or key:B) and (key:B or key:C)', ['B']);
    });

    it('should parse not query', () => {
      assertQueryResult('not key:A', ['B', 'B2', 'C']);
      assertQueryResult('NOT key:A', ['B', 'B2', 'C']);
    });

    it('should parse upstream plus query', () => {
      assertQueryResult('1+key:A', ['A']);
      assertQueryResult('1+key:B', ['A', 'B']);
      assertQueryResult('1+key:C', ['B', 'B2', 'C']);
      assertQueryResult('2+key:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream plus query', () => {
      assertQueryResult('key:A+1', ['A', 'B', 'B2']);
      assertQueryResult('key:A+2', ['A', 'B', 'B2', 'C']);
      assertQueryResult('key:C+1', ['C']);
      assertQueryResult('key:B+1', ['B', 'C']);
    });

    it('should parse upstream star query', () => {
      assertQueryResult('+key:A', ['A']);
      assertQueryResult('+key:B', ['A', 'B']);
      assertQueryResult('+key:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream star query', () => {
      assertQueryResult('key:A+', ['A', 'B', 'B2', 'C']);
      assertQueryResult('key:B+', ['B', 'C']);
      assertQueryResult('key:C+', ['C']);
    });

    it('should parse up and down traversal queries', () => {
      assertQueryResult('key:A+ and +key:C', ['A', 'B', 'B2', 'C']);
      assertQueryResult('+key:B+', ['A', 'B', 'C']);
      assertQueryResult('key:A+ and +key:C and +key:B+', ['A', 'B', 'C']);
      assertQueryResult('key:A+ and +key:B+ and +key:C', ['A', 'B', 'C']);
      assertQueryResult('key:A+ AND +key:B+ AND +key:C', ['A', 'B', 'C']);
    });

    it('should parse sinks query', () => {
      assertQueryResult('sinks(*)', ['C']);
      assertQueryResult('sinks(key:A)', ['A']);
      assertQueryResult('sinks(key:A or key:B)', ['B']);
      assertQueryResult('sinks(key:A OR key:B)', ['B']);
    });

    it('should parse roots query', () => {
      assertQueryResult('roots(*)', ['A']);
      assertQueryResult('roots(key:C)', ['C']);
      assertQueryResult('roots(key:A or key:B)', ['A']);
    });

    it('should parse tag query', () => {
      assertQueryResult('tag:foo', ['B']);
      assertQueryResult('tag:foo=bar', ['A']);
    });

    it('should parse owner query', () => {
      assertQueryResult('owner:"owner@owner.com"', ['A']);
    });

    it('should parse group query', () => {
      assertQueryResult('group:my_group', ['C']);
    });

    it('should parse kind query', () => {
      assertQueryResult('kind:python', ['B']);
      assertQueryResult('kind:snowflake', ['B']);
    });

    it('should parse code location query', () => {
      assertQueryResult('code_location:"repo@my_location"', ['C']);
    });

    it('should be able to filter to assets without any code location', () => {
      assertQueryResult('code_location:<null>', ['B2']);
    });

    it('should be able to filter to assets without any tags', () => {
      assertQueryResult('tag:<null>', ['B2', 'C']);
    });

    it('should be able to filter to assets without any owners', () => {
      assertQueryResult('owner:<null>', ['B', 'B2', 'C']);
    });

    it('should be able to filter to assets without any group', () => {
      assertQueryResult('group:<null>', ['B2']);
    });

    it('should be able to filter to assets without any kind', () => {
      assertQueryResult('kind:<null>', ['A', 'B2', 'C']);
    });
  });
});

const STATIC_DIM = buildDimensionDefinitionType({type: PartitionDefinitionType.STATIC});
const DYNAMIC_DIM = buildDimensionDefinitionType({type: PartitionDefinitionType.DYNAMIC});
const TIME_DIM = buildDimensionDefinitionType({type: PartitionDefinitionType.TIME_WINDOW});

const PARTITIONS_GRAPH: AssetGraphQueryItem[] = [
  {
    name: 'unpartitioned',
    node: buildAssetNode({partitionDefinition: null}),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
  {
    name: 'static_asset',
    node: buildAssetNode({
      partitionDefinition: buildPartitionDefinition({dimensionTypes: [STATIC_DIM]}),
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
  {
    name: 'dynamic_asset',
    node: buildAssetNode({
      partitionDefinition: buildPartitionDefinition({dimensionTypes: [DYNAMIC_DIM]}),
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
  {
    name: 'time_asset',
    node: buildAssetNode({
      partitionDefinition: buildPartitionDefinition({dimensionTypes: [TIME_DIM]}),
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
  {
    name: 'multi_asset',
    node: buildAssetNode({
      partitionDefinition: buildPartitionDefinition({dimensionTypes: [STATIC_DIM, TIME_DIM]}),
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
];

function assertPartitionsQueryResult(query: string, expectedNames: string[]) {
  const result = parseAssetSelectionQuery(PARTITIONS_GRAPH, query);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(result.all.map((asset) => asset.name))).toEqual(new Set(expectedNames));
}

describe('parseAssetSelectionQuery - partitions', () => {
  it('should filter to unpartitioned assets', () => {
    assertPartitionsQueryResult('partitions:none', ['unpartitioned']);
  });

  it('should filter to static partitioned assets', () => {
    assertPartitionsQueryResult('partitions:static', ['static_asset']);
  });

  it('should filter to dynamic partitioned assets', () => {
    assertPartitionsQueryResult('partitions:dynamic', ['dynamic_asset']);
  });

  it('should filter to time-window partitioned assets', () => {
    assertPartitionsQueryResult('partitions:time', ['time_asset']);
  });

  it('should filter to multi-dimensional partitioned assets', () => {
    assertPartitionsQueryResult('partitions:multipartitions', ['multi_asset']);
  });

  it('should handle partitions:<null> as equivalent to partitions:none', () => {
    assertPartitionsQueryResult('partitions:<null>', ['unpartitioned']);
  });

  it('should compose with other filters', () => {
    assertPartitionsQueryResult('partitions:static or partitions:dynamic', [
      'static_asset',
      'dynamic_asset',
    ]);
    assertPartitionsQueryResult('not partitions:none', [
      'static_asset',
      'dynamic_asset',
      'time_asset',
      'multi_asset',
    ]);
  });
});

// automation_type tests

function buildAutomationAsset(name: string): AssetGraphQueryItem {
  return {
    name,
    node: buildAssetNode({assetKey: buildAssetKey({path: [name]})}),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  };
}

const AUTOMATION_GRAPH: AssetGraphQueryItem[] = [
  buildAutomationAsset('no_automation'),
  buildAutomationAsset('with_schedule'),
  buildAutomationAsset('with_sensor'),
  buildAutomationAsset('with_disabled'),
  buildAutomationAsset('with_run_status_sensor'),
];

function buildAutomationSupplementaryData(): SupplementaryInformation {
  const data: Record<string, {path: string[]}[]> = {};

  function addValue(value: string, name: string) {
    const key = getSupplementaryDataKey({field: 'automation_type', value});
    const existing = data[key] ?? [];
    existing.push({path: [name]});
    data[key] = existing;
  }

  // no_automation has none
  addValue('none', 'no_automation');

  // with_schedule has schedule
  addValue('any', 'with_schedule');
  addValue('schedule', 'with_schedule');

  // with_sensor has sensor
  addValue('any', 'with_sensor');
  addValue('sensor', 'with_sensor');
  addValue('sensor/standard', 'with_sensor');

  // with_disabled has a disabled automation
  addValue('any', 'with_disabled');
  addValue('sensor', 'with_disabled');
  addValue('disabled', 'with_disabled');

  // with_run_status_sensor has a run status sensor
  addValue('any', 'with_run_status_sensor');
  addValue('sensor', 'with_run_status_sensor');
  addValue('sensor/run_status', 'with_run_status_sensor');

  return data;
}

const AUTOMATION_SUPPLEMENTARY_DATA = buildAutomationSupplementaryData();

function assertAutomationQueryResult(query: string, expectedNames: string[]) {
  const result = parseAssetSelectionQuery(AUTOMATION_GRAPH, query, AUTOMATION_SUPPLEMENTARY_DATA);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(result.all.map((asset) => asset.name))).toEqual(new Set(expectedNames));
}

describe('parseAssetSelectionQuery - automation_type', () => {
  it('should filter to assets with no automations', () => {
    assertAutomationQueryResult('automation_type:none', ['no_automation']);
  });

  it('should filter to assets with any automation', () => {
    assertAutomationQueryResult('automation_type:any', [
      'with_schedule',
      'with_sensor',
      'with_disabled',
      'with_run_status_sensor',
    ]);
  });

  it('should filter to assets with disabled automations', () => {
    assertAutomationQueryResult('automation_type:disabled', ['with_disabled']);
  });

  it('should filter to assets with schedules', () => {
    assertAutomationQueryResult('automation_type:schedule', ['with_schedule']);
  });

  it('should filter to assets with sensors', () => {
    assertAutomationQueryResult('automation_type:sensor', [
      'with_sensor',
      'with_disabled',
      'with_run_status_sensor',
    ]);
  });

  it('should filter by sensor subtype', () => {
    assertAutomationQueryResult('automation_type:sensor/standard', ['with_sensor']);
    assertAutomationQueryResult('automation_type:sensor/run_status', ['with_run_status_sensor']);
  });

  it('should compose with other filters', () => {
    assertAutomationQueryResult('automation_type:sensor and automation_type:disabled', [
      'with_disabled',
    ]);
    assertAutomationQueryResult('not automation_type:none', [
      'with_schedule',
      'with_sensor',
      'with_disabled',
      'with_run_status_sensor',
    ]);
  });
});

// sensor: and schedule: name filtering tests (supplementary data)

function buildSensorScheduleSupplementaryData(): SupplementaryInformation {
  const data: Record<string, {path: string[]}[]> = {};

  function addValue(field: string, value: string, name: string) {
    const key = getSupplementaryDataKey({field, value});
    const existing = data[key] ?? [];
    existing.push({path: [name]});
    data[key] = existing;
  }

  addValue('sensor', 'my_sensor', 'with_sensor');
  addValue('sensor', 'my_sensor', 'with_run_status_sensor');
  addValue('sensor', 'other_sensor', 'with_disabled');
  addValue('schedule', 'daily_schedule', 'with_schedule');

  return data;
}

const SENSOR_SCHEDULE_SUPPLEMENTARY = buildSensorScheduleSupplementaryData();

describe('parseAssetSelectionQuery - sensor/schedule name', () => {
  it('should filter by sensor name', () => {
    const result = parseAssetSelectionQuery(
      AUTOMATION_GRAPH,
      'sensor:my_sensor',
      SENSOR_SCHEDULE_SUPPLEMENTARY,
    );
    if (result instanceof Error) {
      throw result;
    }
    expect(new Set(result.all.map((a) => a.name))).toEqual(
      new Set(['with_sensor', 'with_run_status_sensor']),
    );
  });

  it('should filter by schedule name', () => {
    const result = parseAssetSelectionQuery(
      AUTOMATION_GRAPH,
      'schedule:daily_schedule',
      SENSOR_SCHEDULE_SUPPLEMENTARY,
    );
    if (result instanceof Error) {
      throw result;
    }
    expect(new Set(result.all.map((a) => a.name))).toEqual(new Set(['with_schedule']));
  });
});

// job: filtering tests (direct node filtering)

const JOB_GRAPH: AssetGraphQueryItem[] = [
  {
    name: 'in_job_a',
    node: buildAssetNode({
      assetKey: buildAssetKey({path: ['in_job_a']}),
      jobNames: ['job_alpha', 'job_beta'],
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
  {
    name: 'in_job_b',
    node: buildAssetNode({
      assetKey: buildAssetKey({path: ['in_job_b']}),
      jobNames: ['job_beta'],
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
  {
    name: 'no_job',
    node: buildAssetNode({
      assetKey: buildAssetKey({path: ['no_job']}),
      jobNames: [],
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: []}],
  },
];

describe('parseAssetSelectionQuery - job', () => {
  it('should filter by job name', () => {
    const result = parseAssetSelectionQuery(JOB_GRAPH, 'job:job_alpha');
    if (result instanceof Error) {
      throw result;
    }
    expect(new Set(result.all.map((a) => a.name))).toEqual(new Set(['in_job_a']));
  });

  it('should match multiple assets in the same job', () => {
    const result = parseAssetSelectionQuery(JOB_GRAPH, 'job:job_beta');
    if (result instanceof Error) {
      throw result;
    }
    expect(new Set(result.all.map((a) => a.name))).toEqual(new Set(['in_job_a', 'in_job_b']));
  });

  it('should return empty for non-existent job', () => {
    const result = parseAssetSelectionQuery(JOB_GRAPH, 'job:nonexistent');
    if (result instanceof Error) {
      throw result;
    }
    expect(result.all).toEqual([]);
  });
});
