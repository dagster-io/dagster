/* eslint-disable jest/expect-expect */

import {RunGraphQueryItem} from '../../gantt/toGraphQueryItems';
import {IStepMetadata, IStepState} from '../../runs/RunMetadataProvider';
import {parseRunSelectionQuery} from '../AntlrRunSelection';

function buildMetadata(state: IStepState): IStepMetadata {
  return {
    state,
    attempts: [],
    markers: [],
    transitions: [],
  };
}

const TEST_GRAPH: RunGraphQueryItem[] = [
  // Top Layer
  {
    name: 'A',
    metadata: buildMetadata(IStepState.SUCCEEDED),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
  },
  // Second Layer
  {
    name: 'B',
    metadata: buildMetadata(IStepState.FAILED),
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },
  {
    name: 'B2',
    metadata: buildMetadata(IStepState.SKIPPED),
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },
  // Third Layer
  {
    name: 'C',
    metadata: buildMetadata(IStepState.RUNNING),
    inputs: [{dependsOn: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
    outputs: [{dependedBy: []}],
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseRunSelectionQuery(TEST_GRAPH, query);
  expect(result).not.toBeInstanceOf(Error);
  if (result instanceof Error) {
    throw result;
  }
  expect(result.all.length).toBe(expectedNames.length);
  expect(new Set(result.all.map((run) => run.name))).toEqual(new Set(expectedNames));
}

// Most tests copied from AntlrAssetSelection.test.ts
describe('parseRunSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(parseRunSelectionQuery(TEST_GRAPH, 'A')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'name:A name:B')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'not')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'and')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'name:A and')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'sinks')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'notafunction()')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'tag:foo=')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'owner')).toBeInstanceOf(Error);
      expect(parseRunSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toBeInstanceOf(Error);
    });
  });

  describe('valid queries', () => {
    it('should parse star query', () => {
      assertQueryResult('*', ['A', 'B', 'B2', 'C']);
    });

    it('should parse name query', () => {
      assertQueryResult('name:A', ['A']);
    });

    it('should parse name_substring query', () => {
      assertQueryResult('name_substring:A', ['A']);
      assertQueryResult('name_substring:B', ['B', 'B2']);
    });

    it('should parse and query', () => {
      assertQueryResult('name:A and name:B', []);
      assertQueryResult('name:A and name:B and name:C', []);
    });

    it('should parse or query', () => {
      assertQueryResult('name:A or name:B', ['A', 'B']);
      assertQueryResult('name:A or name:B or name:C', ['A', 'B', 'C']);
      assertQueryResult('(name:A or name:B) and (name:B or name:C)', ['B']);
    });

    it('should parse upstream plus query', () => {
      assertQueryResult('1+name:A', ['A']);
      assertQueryResult('1+name:B', ['A', 'B']);
      assertQueryResult('1+name:C', ['B', 'B2', 'C']);
      assertQueryResult('2+name:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream plus query', () => {
      assertQueryResult('name:A+1', ['A', 'B', 'B2']);
      assertQueryResult('name:A+2', ['A', 'B', 'B2', 'C']);
      assertQueryResult('name:C+1', ['C']);
      assertQueryResult('name:B+1', ['B', 'C']);
    });

    it('should parse upstream star query', () => {
      assertQueryResult('+name:A', ['A']);
      assertQueryResult('+name:B', ['A', 'B']);
      assertQueryResult('+name:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream star query', () => {
      assertQueryResult('name:A+', ['A', 'B', 'B2', 'C']);
      assertQueryResult('name:B+', ['B', 'C']);
      assertQueryResult('name:C+', ['C']);
    });

    it('should parse up and down traversal queries', () => {
      assertQueryResult('name:A+ and +name:C', ['A', 'B', 'B2', 'C']);
      assertQueryResult('+name:B+', ['A', 'B', 'C']);
      assertQueryResult('name:A+ and +name:C and +name:B+', ['A', 'B', 'C']);
      assertQueryResult('name:A+ and +name:B+ and +name:C', ['A', 'B', 'C']);
    });

    it('should parse sinks query', () => {
      assertQueryResult('sinks(*)', ['C']);
      assertQueryResult('sinks(name:A)', ['A']);
      assertQueryResult('sinks(name:A or name:B)', ['B']);
    });

    it('should parse roots query', () => {
      assertQueryResult('roots(*)', ['A']);
      assertQueryResult('roots(name:C)', ['C']);
      assertQueryResult('roots(name:A or name:B)', ['A']);
    });

    it('should parse status query', () => {
      assertQueryResult('status:succeeded', ['A']);
      assertQueryResult('status:SUCCEEDED', ['A']);
      assertQueryResult('status:failed', ['B']);
      assertQueryResult('status:skipped', ['B2']);
      assertQueryResult('status:"running"', ['C']);
      assertQueryResult('status:not_a_status', []);
    });
  });
});
