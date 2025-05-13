import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {
  buildAutomationConditionEvaluationNode,
  buildPartitionedAssetConditionEvaluationNode,
  buildUnpartitionedAssetConditionEvaluationNode,
} from '../../../graphql/types';
import {PolicyEvaluationTable} from '../PolicyEvaluationTable';

describe('PolicyEvaluationTable', () => {
  it('renders legacy non-partitioned table for non-partitioned `isLegacy` evaluation', () => {
    const nodes = [
      buildUnpartitionedAssetConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'a',
        description: 'some condition',
      }),
    ];

    render(
      <PolicyEvaluationTable
        evaluationNodes={nodes}
        assetKeyPath={['foo', 'bar']}
        evaluationId="1"
        rootUniqueId="a"
        isLegacyEvaluation
        selectPartition={() => {}}
      />,
    );

    expect(screen.getByRole('columnheader', {name: /condition/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /result/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /duration/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /details/i})).toBeVisible();

    expect(screen.getByRole('cell', {name: /some condition/i})).toBeVisible();
  });

  it('renders legacy partitioned table for partitioned `isLegacy` evaluation', () => {
    const nodes = [
      buildPartitionedAssetConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'a',
        description: 'hi i am partitioned',
        numCandidates: 3,
      }),
    ];

    render(
      <PolicyEvaluationTable
        evaluationNodes={nodes}
        assetKeyPath={['foo', 'bar']}
        evaluationId="1"
        rootUniqueId="a"
        isLegacyEvaluation
        selectPartition={() => {}}
      />,
    );

    expect(screen.getByRole('columnheader', {name: /condition/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /partitions evaluated/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /result/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /duration/i})).toBeVisible();

    expect(screen.getByRole('cell', {name: /hi i am partitioned/i})).toBeVisible();
  });

  it('renders new table for non-legacy evaluation', async () => {
    const nodes = [
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'a',
        userLabel: 'my user label',
        isPartitioned: false,
      }),
    ];

    render(
      <PolicyEvaluationTable
        evaluationNodes={nodes}
        assetKeyPath={['foo', 'bar']}
        evaluationId="1"
        rootUniqueId="a"
        isLegacyEvaluation={false}
        selectPartition={() => {}}
      />,
    );

    expect(screen.getByRole('columnheader', {name: /condition/i})).toBeVisible();

    // `isPartitioned` is false, so no column for that.
    expect(screen.queryByRole('columnheader', {name: /partitions evaluated/i})).toBeNull();

    expect(screen.getByRole('columnheader', {name: /result/i})).toBeVisible();
    expect(screen.getByRole('columnheader', {name: /duration/i})).toBeVisible();

    expect(screen.getByRole('cell', {name: /my user label/i})).toBeVisible();
  });

  describe('Row expansion', () => {
    it('toggles rows in legacy table', async () => {
      const user = userEvent.setup();
      const nodes = [
        buildUnpartitionedAssetConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'a',
          description: 'parent condition',
          childUniqueIds: ['b'],
        }),
        buildUnpartitionedAssetConditionEvaluationNode({
          startTimestamp: 2,
          endTimestamp: 8,
          uniqueId: 'b',
          description: 'child condition',
        }),
      ];

      render(
        <PolicyEvaluationTable
          evaluationNodes={nodes}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="a"
          isLegacyEvaluation
          selectPartition={() => {}}
        />,
      );

      const parentRow = screen.getByRole('cell', {name: /parent condition/i});

      // In legacy table, rows are expanded by default.
      expect(screen.getByRole('cell', {name: /child condition/i})).toBeVisible();

      await user.click(parentRow);

      expect(screen.queryByRole('cell', {name: /child condition/i})).toBeNull();

      // Parent condition remains visible.
      expect(screen.getByRole('cell', {name: /parent condition/i})).toBeVisible();
    });

    it('toggles rows in new table', async () => {
      const user = userEvent.setup();
      const nodes = [
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'a',
          userLabel: 'parent condition',
          isPartitioned: false,
          numTrue: 0,
          childUniqueIds: ['b'],
        }),
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'b',
          userLabel: 'child condition',
          numTrue: 0,
          isPartitioned: false,
        }),
      ];

      render(
        <PolicyEvaluationTable
          evaluationNodes={nodes}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="a"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      const parentRow = screen.getByRole('cell', {name: /parent condition/i});

      // In new table, rows are collapsed by default.
      expect(screen.queryByRole('cell', {name: /child condition/i})).toBeNull();

      await user.click(parentRow);

      // Both conditions visible.
      expect(screen.getByRole('cell', {name: /child condition/i})).toBeVisible();
      expect(screen.getByRole('cell', {name: /parent condition/i})).toBeVisible();
    });
  });
});
