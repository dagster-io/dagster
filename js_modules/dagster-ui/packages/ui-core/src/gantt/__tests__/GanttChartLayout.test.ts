import {IRunMetadataDict, IStepState} from '../../runs/RunMetadataProvider';
import {GanttChartLayout, GanttChartLayoutOptions} from '../Constants';
import {GanttChartMode} from '../GanttChart';
import {adjustLayoutWithRunMetadata, buildLayout, interestingQueriesFor} from '../GanttChartLayout';

describe('buildLayout', () => {
  it('ignores self-dependencies caused by TimeWindowPartitionMapping', () => {
    const result = buildLayout({
      mode: GanttChartMode.FLAT,
      nodes: [
        {
          name: 'depends_on_nothing',
          inputs: [],
          outputs: [{dependedBy: [{solid: {name: 'depends_on_yesterday'}}]}],
        },
        {
          name: 'depends_on_yesterday',
          inputs: [
            {dependsOn: [{solid: {name: 'depends_on_nothing'}}]},
            {dependsOn: [{solid: {name: 'depends_on_yesterday'}}]},
          ],
          outputs: [{dependedBy: [{solid: {name: 'depends_on_yesterday'}}]}],
        },
      ],
    });

    expect(result.markers).toEqual([]);
    expect(result.boxes.length).toEqual(2);
    expect(result.boxes[0]).toMatchObject({
      key: 'depends_on_nothing',
      root: true,
      state: undefined,
      width: 200,
      x: 16,
      y: 0,
    });
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(result.boxes[0]!.children.length).toEqual(1);
    expect(result.boxes[1]).toMatchObject({
      key: 'depends_on_yesterday',
      root: false,
      state: undefined,
      width: 200,
      x: 252,
      y: 1,
    });
  });

  it('collapses boxes onto same row when possible (WATERFALL mode)', () => {
    // Create a diamond dependency: A -> B, A -> C, B -> D, C -> D
    // This exercises the collapse loop with onTargetY and boxesByY lookups
    const result = buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        {
          name: 'A',
          inputs: [],
          outputs: [{dependedBy: [{solid: {name: 'B'}}, {solid: {name: 'C'}}]}],
        },
        {
          name: 'B',
          inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
          outputs: [{dependedBy: [{solid: {name: 'D'}}]}],
        },
        {
          name: 'C',
          inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
          outputs: [{dependedBy: [{solid: {name: 'D'}}]}],
        },
        {
          name: 'D',
          inputs: [{dependsOn: [{solid: {name: 'B'}}, {solid: {name: 'C'}}]}],
          outputs: [],
        },
      ],
    });

    expect(result.boxes.length).toEqual(4);
    // Verify the layout was created with proper structure
    const boxA = result.boxes.find((b) => b.key === 'A');
    const boxD = result.boxes.find((b) => b.key === 'D');
    expect(boxA?.root).toBe(true);
    expect(boxD?.root).toBe(false);
    // D should be positioned after B and C
    expect(boxD?.x).toBeGreaterThan(boxA?.x ?? 0);
  });
});

describe('adjustLayoutWithRunMetadata', () => {
  const createBasicLayout = (): GanttChartLayout => {
    return buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        {
          name: 'step_a',
          inputs: [],
          outputs: [{dependedBy: [{solid: {name: 'step_b'}}]}],
        },
        {
          name: 'step_b',
          inputs: [{dependsOn: [{solid: {name: 'step_a'}}]}],
          outputs: [],
        },
      ],
    });
  };

  it('clones layout and applies run metadata in WATERFALL mode', () => {
    const layout = createBasicLayout();
    const options: GanttChartLayoutOptions = {
      mode: GanttChartMode.WATERFALL,
      zoom: 1,
      hideWaiting: false,
      hideTimedMode: false,
      hideUnselectedSteps: false,
    };
    const metadata: IRunMetadataDict = {
      firstLogAt: 1000,
      mostRecentLogAt: 2000,
      globalMarkers: [],
      steps: {
        step_a: {
          state: IStepState.SUCCEEDED,
          transitions: [{state: IStepState.SUCCEEDED, time: 1500}],
          attempts: [{start: 1000, end: 1500, exitState: IStepState.SUCCEEDED}],
          markers: [],
        },
      },
    };

    const result = adjustLayoutWithRunMetadata(layout, options, metadata, 1, 2000);

    // Verify layout was cloned (not same reference)
    expect(result).not.toBe(layout);
    expect(result.boxes).not.toBe(layout.boxes);
    // Verify step_a has state applied
    const stepA = result.boxes.find((b) => b.node.name === 'step_a');
    expect(stepA?.state).toBe(IStepState.SUCCEEDED);
  });

  it('handles retries by splitting boxes in WATERFALL_TIMED mode', () => {
    const layout = createBasicLayout();
    const options: GanttChartLayoutOptions = {
      mode: GanttChartMode.WATERFALL_TIMED,
      zoom: 1,
      hideWaiting: false,
      hideTimedMode: false,
      hideUnselectedSteps: false,
    };
    const metadata: IRunMetadataDict = {
      firstLogAt: 1000,
      mostRecentLogAt: 3000,
      startedPipelineAt: 1000,
      globalMarkers: [],
      steps: {
        step_a: {
          state: IStepState.SUCCEEDED,
          transitions: [],
          attempts: [
            {start: 1000, end: 1500, exitState: IStepState.FAILED},
            {start: 1600, end: 2000, exitState: IStepState.SUCCEEDED},
          ],
          markers: [],
        },
      },
    };

    const result = adjustLayoutWithRunMetadata(layout, options, metadata, 0.01, 3000);

    // With 2 attempts, step_a should be split into 2 boxes
    const stepABoxes = result.boxes.filter((b) => b.node.name === 'step_a');
    expect(stepABoxes.length).toBe(2);
    // Verify both states are present (order may vary based on implementation)
    const states = stepABoxes.map((b) => b.state);
    expect(states).toContain(IStepState.FAILED);
    expect(states).toContain(IStepState.SUCCEEDED);
  });
});

describe('interestingQueriesFor', () => {
  it('returns undefined for empty layout', () => {
    const metadata: IRunMetadataDict = {
      firstLogAt: 0,
      mostRecentLogAt: 0,
      globalMarkers: [],
      steps: {},
    };
    const layout: GanttChartLayout = {boxes: [], markers: []};

    const result = interestingQueriesFor(metadata, layout);
    expect(result).toBeUndefined();
  });

  it('returns errors query for failed steps', () => {
    const layout = buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        {name: 'step_a', inputs: [], outputs: []},
        {name: 'step_b', inputs: [], outputs: []},
      ],
    });
    const metadata: IRunMetadataDict = {
      firstLogAt: 1000,
      mostRecentLogAt: 2000,
      globalMarkers: [],
      steps: {
        step_a: {
          state: IStepState.FAILED,
          transitions: [],
          attempts: [],
          markers: [],
        },
        step_b: {
          state: IStepState.SUCCEEDED,
          transitions: [],
          attempts: [],
          markers: [],
        },
      },
    };

    const result = interestingQueriesFor(metadata, layout);
    const errorsQuery = result?.find((r) => r.name === 'Errors');
    expect(errorsQuery?.value).toBe('+step_a');
  });

  it('returns slowest steps query sorted by duration', () => {
    const layout = buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        {name: 'fast_step', inputs: [], outputs: []},
        {name: 'slow_step', inputs: [], outputs: []},
      ],
    });
    const metadata: IRunMetadataDict = {
      firstLogAt: 1000,
      mostRecentLogAt: 5000,
      globalMarkers: [],
      steps: {
        fast_step: {
          state: IStepState.SUCCEEDED,
          start: 1000,
          end: 1100, // 100ms duration
          transitions: [],
          attempts: [],
          markers: [],
        },
        slow_step: {
          state: IStepState.SUCCEEDED,
          start: 1000,
          end: 3000, // 2000ms duration
          transitions: [],
          attempts: [],
          markers: [],
        },
      },
    };

    const result = interestingQueriesFor(metadata, layout);
    const slowestQuery = result?.find((r) => r.name === 'Slowest Individual Steps');
    // slow_step should come first (longer duration)
    expect(slowestQuery?.value).toMatch(/^"slow_step"/);
  });
});
