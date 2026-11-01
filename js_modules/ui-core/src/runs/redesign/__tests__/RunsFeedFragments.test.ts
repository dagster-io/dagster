import {FieldNode, Kind, visit} from 'graphql';

import {RUNS_FEED_ENTRY_FRAGMENT} from '../RunsFeedFragments';

describe('Runs feed fragments', () => {
  it('bounds both Run selection previews', () => {
    const previews: FieldNode[] = [];
    visit(RUNS_FEED_ENTRY_FRAGMENT, {
      Field(node) {
        if (['assetSelection', 'assetCheckSelection'].includes(node.name.value)) {
          previews.push(node);
        }
      },
    });
    expect(previews.map((node) => node.name.value).sort()).toEqual([
      'assetCheckSelection',
      'assetSelection',
    ]);
    expect(
      previews.map(
        (node) => node.arguments?.find((argument) => argument.name.value === 'limit')?.value,
      ),
    ).toMatchObject([
      {kind: Kind.INT, value: '25'},
      {kind: Kind.INT, value: '25'},
    ]);
  });

  it('keeps expensive Run and Backfill detail fields out of feed requests', () => {
    const detailFields = new Set([
      'executionPlan',
      'runConfigYaml',
      'eventConnection',
      'stats',
      'stepStats',
      'runs',
      'reexecutionSteps',
      'partitionNames',
      'partitionSet',
      'numPartitions',
      'numCancelable',
      'isValidSerialization',
      'partitionStatuses',
      'partitionStatusCounts',
      'assetBackfillData',
      'assetMaterializations',
      'assetObservations',
    ]);
    const selectedDetailFields: string[] = [];
    visit(RUNS_FEED_ENTRY_FRAGMENT, {
      Field(node) {
        if (detailFields.has(node.name.value)) {
          selectedDetailFields.push(node.name.value);
        }
      },
    });
    expect(selectedDetailFields).toEqual([]);
  });
});
