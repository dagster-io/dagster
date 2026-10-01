import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {
  buildAutomationConditionEvaluationNode,
  buildPartitionedAssetConditionEvaluationNode,
  buildSinceConditionMetadata,
  buildUnpartitionedAssetConditionEvaluationNode,
} from '../../../graphql/builders';
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
        operatorType: 'identity',
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

  describe('history-dependent node rendering', () => {
    const newlyTrueNodes = ({edgeIsTrue}: {edgeIsTrue: boolean}) => [
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'newly',
        userLabel: 'newly_missing',
        expandedLabel: ['NEWLY_TRUE', '(missing)'],
        childUniqueIds: ['operand'],
        isPartitioned: false,
        numTrue: edgeIsTrue ? 1 : 0,
        numCandidates: null,
        operatorType: 'identity',
      }),
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'operand',
        userLabel: 'the operand row',
        expandedLabel: ['missing'],
        childUniqueIds: [],
        isPartitioned: false,
        numTrue: 1,
        numCandidates: null,
        operatorType: 'identity',
      }),
    ];

    it('renders current/last tick memory rows for a false edge over a true operand', async () => {
      render(
        <PolicyEvaluationTable
          evaluationNodes={newlyTrueNodes({edgeIsTrue: false})}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="newly"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      expect(await screen.findByText('newly_missing')).toBeVisible();
      // memory rows replace the operand's own (current-value) row
      expect(await screen.findByText('current tick')).toBeVisible();
      expect(await screen.findByText('last tick')).toBeVisible();
      expect(await screen.findAllByText('the operand row')).toHaveLength(2);
      // the operand was true on both ticks; the edge itself is false
      expect(await screen.findAllByText('True')).toHaveLength(2);
      expect(await screen.findAllByText('False')).toHaveLength(1);
    });

    it('renders a true edge as a false-to-true transition', async () => {
      render(
        <PolicyEvaluationTable
          evaluationNodes={newlyTrueNodes({edgeIsTrue: true})}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="newly"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      // the edge and the current tick are true; the last tick is false
      expect(await screen.findByText('current tick')).toBeVisible();
      expect(await screen.findByText('last tick')).toBeVisible();
      expect(await screen.findAllByText('True')).toHaveLength(2);
      expect(await screen.findAllByText('False')).toHaveLength(1);
    });

    it('renders set/reset memory rows for a since latch', async () => {
      const nodes = [
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'since',
          userLabel: null,
          expandedLabel: ['(newly_updated)', 'SINCE', '(newly_requested)'],
          childUniqueIds: ['trigger', 'reset'],
          isPartitioned: false,
          numTrue: 1,
          numCandidates: null,
          operatorType: 'identity',
          sinceMetadata: buildSinceConditionMetadata({
            triggerTimestamp: 1719777600,
            triggerEvaluationId: '42',
            resetTimestamp: null,
            resetEvaluationId: null,
          }),
        }),
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'trigger',
          userLabel: 'newly_updated',
          expandedLabel: ['newly_updated'],
          childUniqueIds: [],
          isPartitioned: false,
          numTrue: 0,
          numCandidates: null,
          operatorType: 'identity',
        }),
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'reset',
          userLabel: 'newly_requested',
          expandedLabel: ['newly_requested'],
          childUniqueIds: [],
          isPartitioned: false,
          numTrue: 0,
          numCandidates: null,
          operatorType: 'identity',
        }),
      ];

      render(
        <PolicyEvaluationTable
          evaluationNodes={nodes}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="since"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      // set/reset tags replace the operands' current-value rows
      expect(await screen.findByText(/^set at /)).toBeVisible();
      expect(await screen.findByText('reset: never')).toBeVisible();
      // each operand appears in the parent label and once as a memory row
      expect(await screen.findAllByText('newly_updated')).toHaveLength(2);
      expect(await screen.findAllByText('newly_requested')).toHaveLength(2);
      // the latch and its set row are true; the never-fired reset row is false
      expect(await screen.findAllByText('True')).toHaveLength(2);
      expect(await screen.findAllByText('False')).toHaveLength(1);
    });

    const partitionedNewlyTrueNodes = ({numCandidates}: {numCandidates: number | null}) => [
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'newly',
        userLabel: 'newly_missing',
        expandedLabel: ['NEWLY_TRUE', '(missing)'],
        childUniqueIds: ['operand'],
        isPartitioned: true,
        numTrue: 2,
        numCandidates,
        operatorType: 'identity',
      }),
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'operand',
        userLabel: 'the operand row',
        expandedLabel: ['missing'],
        childUniqueIds: [],
        isPartitioned: true,
        numTrue: 5,
        numCandidates: null,
        operatorType: 'identity',
      }),
    ];

    it('renders partitioned memory rows with an "already true" count', async () => {
      render(
        <PolicyEvaluationTable
          evaluationNodes={partitionedNewlyTrueNodes({numCandidates: null})}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="newly"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      // the derived count is |true now ∩ true last tick|, so the tag says "already true"
      // rather than claiming to be the operand's full previous-tick value
      expect(await screen.findByText('current tick')).toBeVisible();
      expect(await screen.findByText('already true')).toBeVisible();
      expect(screen.queryByText('last tick')).toBeNull();
      expect(await screen.findByText('5 True')).toBeVisible();
      expect(await screen.findByText('3 True')).toBeVisible();
    });

    it('omits the "already true" count when the edge was evaluated against narrowed candidates', async () => {
      render(
        <PolicyEvaluationTable
          evaluationNodes={partitionedNewlyTrueNodes({numCandidates: 3})}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="newly"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      expect(await screen.findByText('already true')).toBeVisible();
      // the subtraction (5 - 2 = 3) would overcount under a narrowed candidate set, so the
      // "already true" row renders no count at all
      expect(await screen.findByText('5 True')).toBeVisible();
      expect(screen.queryByText('3 True')).toBeNull();
    });
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
          operatorType: 'identity',
        }),
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'b',
          userLabel: 'child condition',
          numTrue: 0,
          isPartitioned: false,
          operatorType: 'identity',
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

      // In new table, rows are expanded by default, depending on the critical path.
      expect(screen.getByRole('cell', {name: /child condition/i})).toBeVisible();
      expect(screen.getByRole('cell', {name: /parent condition/i})).toBeVisible();

      await user.click(parentRow);

      // Parent condition remains visible, but collapsed so child is not visible.
      expect(screen.queryByRole('cell', {name: /child condition/i})).toBeNull();
      expect(screen.getByRole('cell', {name: /parent condition/i})).toBeVisible();
    });
  });

  describe('Expand/collapse all', () => {
    // Skipped conditions (no true partitions, no candidates) are not expanded by default, so the
    // tree starts fully collapsed.
    const buildNestedNodes = () => [
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'a',
        userLabel: 'root condition',
        isPartitioned: false,
        numTrue: 0,
        numCandidates: 0,
        childUniqueIds: ['b'],
        operatorType: 'identity',
      }),
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'b',
        userLabel: 'middle condition',
        isPartitioned: false,
        numTrue: 0,
        numCandidates: 0,
        childUniqueIds: ['c'],
        operatorType: 'and',
      }),
      buildAutomationConditionEvaluationNode({
        startTimestamp: 0,
        endTimestamp: 10,
        uniqueId: 'c',
        userLabel: 'leaf condition',
        isPartitioned: false,
        numTrue: 0,
        numCandidates: 0,
        operatorType: 'identity',
      }),
    ];

    it('expands every condition group, then collapses them all', async () => {
      const user = userEvent.setup();

      render(
        <PolicyEvaluationTable
          evaluationNodes={buildNestedNodes()}
          assetKeyPath={['foo', 'bar']}
          evaluationId="1"
          rootUniqueId="a"
          isLegacyEvaluation={false}
          selectPartition={() => {}}
        />,
      );

      const toggle = screen.getByRole('button', {name: /condition/i});

      // Starts collapsed: only the root row is present.
      expect(toggle).toHaveAttribute('aria-expanded', 'false');
      expect(screen.getByRole('cell', {name: /root condition/i})).toBeVisible();
      expect(screen.queryByRole('cell', {name: /middle condition/i})).toBeNull();

      await user.click(toggle);

      expect(toggle).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByRole('cell', {name: /root condition/i})).toBeVisible();
      expect(screen.getByRole('cell', {name: /middle condition/i})).toBeVisible();
      expect(screen.getByRole('cell', {name: /leaf condition/i})).toBeVisible();

      await user.click(toggle);

      // Only the root row remains once everything is collapsed.
      expect(toggle).toHaveAttribute('aria-expanded', 'false');
      expect(screen.getByRole('cell', {name: /root condition/i})).toBeVisible();
      expect(screen.queryByRole('cell', {name: /middle condition/i})).toBeNull();
      expect(screen.queryByRole('cell', {name: /leaf condition/i})).toBeNull();
    });

    it('shows no toggle when there is nothing to expand', () => {
      const nodes = [
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 10,
          uniqueId: 'a',
          userLabel: 'only condition',
          isPartitioned: false,
          numTrue: 0,
          numCandidates: 0,
          childUniqueIds: [],
          operatorType: 'identity',
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

      // The column header still reads "Condition", but is not a button.
      expect(screen.getByRole('columnheader', {name: /condition/i})).toBeVisible();
      expect(screen.queryByRole('button', {name: /condition/i})).toBeNull();
    });
  });
});
