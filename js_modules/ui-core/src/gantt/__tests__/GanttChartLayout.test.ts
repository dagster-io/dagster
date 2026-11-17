import {IRunMetadataDict, IStepState} from '../../runs/RunMetadataProvider';
import {GanttChartLayout, GanttChartLayoutOptions, IGanttNode} from '../Constants';
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

const node = (name: string, dependsOn: string[], dependedBy: string[]): IGanttNode => ({
  name,
  inputs: [{dependsOn: dependsOn.map((dep) => ({solid: {name: dep}}))}],
  outputs: [{dependedBy: dependedBy.map((dep) => ({solid: {name: dep}}))}],
});

const chain = (length: number) =>
  Array.from({length}, (_, stepIndex) =>
    node(
      `step_${stepIndex}`,
      stepIndex > 0 ? [`step_${stepIndex - 1}`] : [],
      stepIndex < length - 1 ? [`step_${stepIndex + 1}`] : [],
    ),
  );

describe('buildLayout row collapsing', () => {
  it('collapses a long chain onto a single row', () => {
    const {boxes} = buildLayout({mode: GanttChartMode.WATERFALL, nodes: chain(40)});

    expect(boxes.map((b) => b.y)).toEqual(boxes.map(() => 0));
    const xs = boxes.map((b) => b.x);
    expect(xs).toEqual([...xs].sort((a, b) => a - b));
    expect(new Set(xs).size).toBe(40);
  });

  it('numbers rows without gaps after collapsing (WATERFALL mode)', () => {
    const {boxes} = buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        node('a', [], ['b', 'c', 'd']),
        node('b', ['a'], ['e']),
        node('c', ['a'], ['e']),
        node('d', ['a'], []),
        node('e', ['b', 'c'], ['f']),
        node('f', ['e'], []),
      ],
    });

    const rows = [...new Set(boxes.map((b) => b.y))].sort((a, b) => a - b);
    expect(rows).toEqual(rows.map((_, rowIndex) => rowIndex));
    expect(rows.length).toBeLessThan(boxes.length);
  });

  it('hides a planned dynamic step once a resolved step for it exists', () => {
    const {boxes} = buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        node('emit', [], ['work[0]', 'work[1]', 'work[?]']),
        node('work[0]', ['emit'], []),
        node('work[1]', ['emit'], []),
        node('work[?]', ['emit'], []),
      ],
    });

    expect(boxes.map((b) => b.key)).toEqual(['emit', 'work[0]', 'work[1]']);
  });

  it('keeps the first row of a dynamic fan-out on separate rows', () => {
    const {boxes} = buildLayout({
      mode: GanttChartMode.WATERFALL,
      nodes: [
        node('emit', [], ['work[0]', 'work[1]', 'work[2]']),
        node('work[0]', ['emit'], ['next[0]']),
        node('work[1]', ['emit'], ['next[1]']),
        node('work[2]', ['emit'], ['next[2]']),
        node('next[0]', ['work[0]'], []),
        node('next[1]', ['work[1]'], []),
        node('next[2]', ['work[2]'], []),
      ],
    });

    const yOf = (key: string) => boxes.find((b) => b.key === key)?.y;
    expect(new Set(['work[0]', 'work[1]', 'work[2]'].map(yOf)).size).toBe(3);
    // Downstream steps still collapse onto the row of the step they follow.
    expect(yOf('next[1]')).toBe(yOf('work[1]'));
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

describe('adjustLayoutWithRunMetadata untimed steps and markers', () => {
  const options: GanttChartLayoutOptions = {
    mode: GanttChartMode.WATERFALL_TIMED,
    zoom: 1,
    hideWaiting: false,
    hideTimedMode: false,
    hideUnselectedSteps: false,
  };

  it('places steps that have not started after the current time', () => {
    const layout = buildLayout({mode: GanttChartMode.WATERFALL_TIMED, nodes: chain(4)});
    const metadata: IRunMetadataDict = {
      firstLogAt: 1000,
      mostRecentLogAt: 2000,
      startedPipelineAt: 1000,
      globalMarkers: [],
      steps: {
        step_0: {
          state: IStepState.SUCCEEDED,
          transitions: [],
          attempts: [{start: 1000, end: 1500, exitState: IStepState.SUCCEEDED}],
          markers: [],
        },
        step_1: {
          state: IStepState.RUNNING,
          transitions: [],
          attempts: [{start: 1500}],
          markers: [{key: 'compute', start: 1600, end: 1700}],
        },
      },
    };

    const result = adjustLayoutWithRunMetadata(layout, options, metadata, 1, 2000);
    const boxFor = (name: string) => result.boxes.find((b) => b.node.name === name);

    // The "now" line sits at LEFT_INSET + (2000 - 1000) * scale.
    const nowX = 16 + 1000;
    expect(boxFor('step_2')?.x).toBeGreaterThan(nowX);
    expect(boxFor('step_3')?.x).toBeGreaterThan(boxFor('step_2')?.x ?? Infinity);
    expect(result.markers).toEqual([
      {key: 'step_1:compute', y: boxFor('step_1')?.y, x: 16 + 600, width: 100},
    ]);
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

// Exact positions recorded from a known-good layout. They pin down row and column choices that
// the property tests above don't.
const GOLDEN_LAYOUTS: {
  name: string;
  names: string[];
  edges: [string, string][];
  waterfall: [string, number, number][];
  flat: [string, number, number][];
}[] = [
  {
    name: 'a chain with a shortcut from the root to its tail',
    names: ['R', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8'],
    edges: [
      ['R', 'n1'],
      ['n1', 'n2'],
      ['n2', 'n3'],
      ['n3', 'n4'],
      ['n4', 'n5'],
      ['n5', 'n6'],
      ['n6', 'n7'],
      ['n7', 'n8'],
      ['R', 'n8'],
    ],
    waterfall: [
      ['R', 16, 0],
      ['n1', 236, 1],
      ['n2', 456, 1],
      ['n3', 676, 1],
      ['n4', 896, 1],
      ['n5', 1116, 1],
      ['n6', 1336, 1],
      ['n7', 1556, 1],
      ['n8', 1776, 1],
    ],
    flat: [
      ['R', 16, 0],
      ['n1', 32, 1],
      ['n2', 48, 2],
      ['n3', 64, 3],
      ['n4', 80, 4],
      ['n5', 96, 5],
      ['n6', 112, 6],
      ['n7', 128, 7],
      ['n8', 144, 8],
    ],
  },
  {
    name: 'a chain whose tail feeds back into an early sibling',
    names: ['A', 'B', 'C', 'D', 'X'],
    edges: [
      ['A', 'B'],
      ['B', 'C'],
      ['C', 'D'],
      ['A', 'X'],
      ['D', 'X'],
    ],
    waterfall: [
      ['A', 16, 0],
      ['B', 236, 1],
      ['C', 456, 1],
      ['D', 676, 1],
      ['X', 896, 1],
    ],
    flat: [
      ['A', 16, 0],
      ['B', 32, 1],
      ['C', 48, 2],
      ['D', 64, 3],
      ['X', 80, 4],
    ],
  },
  {
    name: 'a sink with parents at different depths',
    names: ['R', 'a1', 'b1', 'b2', 'c1', 'c2', 'c3', 'S'],
    edges: [
      ['R', 'a1'],
      ['R', 'b1'],
      ['b1', 'b2'],
      ['R', 'c1'],
      ['c1', 'c2'],
      ['c2', 'c3'],
      ['a1', 'S'],
      ['b2', 'S'],
      ['c3', 'S'],
      ['b1', 'S'],
    ],
    waterfall: [
      ['R', 16, 0],
      ['a1', 236, 1],
      ['b1', 236, 2],
      ['c1', 236, 0],
      ['b2', 456, 3],
      ['c2', 456, 0],
      ['c3', 676, 0],
      ['S', 896, 3],
    ],
    flat: [
      ['R', 16, 0],
      ['c1', 32, 1],
      ['c2', 48, 2],
      ['c3', 64, 3],
      ['a1', 32, 4],
      ['b1', 32, 5],
      ['b2', 48, 6],
      ['S', 64, 7],
    ],
  },
  {
    name: 'a self-dependency in the middle of a chain',
    names: ['R', 'm1', 'm2', 'm3', 'Z'],
    edges: [
      ['R', 'm1'],
      ['m1', 'm2'],
      ['m2', 'm2'],
      ['m2', 'm3'],
      ['R', 'Z'],
      ['Z', 'm3'],
    ],
    waterfall: [
      ['R', 16, 0],
      ['m1', 236, 1],
      ['Z', 236, 0],
      ['m2', 456, 2],
      ['m3', 676, 2],
    ],
    flat: [
      ['R', 16, 0],
      ['Z', 32, 1],
      ['m1', 32, 2],
      ['m2', 472, 3],
      ['m3', 488, 4],
    ],
  },
  {
    name: 'resolved and planned dynamic steps across two levels',
    names: ['s', 'a[0]', 'a[1]', 'a[?]', 'b[0]', 'b[?]', 'b[1]', 'join'],
    edges: [
      ['s', 'a[0]'],
      ['s', 'a[?]'],
      ['s', 'a[1]'],
      ['a[0]', 'b[0]'],
      ['a[?]', 'b[?]'],
      ['a[1]', 'b[1]'],
      ['b[0]', 'join'],
      ['b[1]', 'join'],
    ],
    waterfall: [
      ['s', 16, 0],
      ['a[0]', 236, 1],
      ['a[1]', 236, 2],
      ['b[0]', 456, 1],
      ['b[1]', 456, 2],
      ['join', 676, 2],
    ],
    flat: [
      ['s', 16, 0],
      ['a[0]', 32, 1],
      ['b[0]', 48, 2],
      ['a[1]', 32, 3],
      ['b[1]', 48, 4],
      ['join', 64, 5],
    ],
  },
];

const nodesFor = (names: string[], edges: [string, string][]): IGanttNode[] =>
  names.map((name) => ({
    name,
    inputs: [
      {dependsOn: edges.filter(([, to]) => to === name).map(([from]) => ({solid: {name: from}}))},
    ],
    outputs: [
      {dependedBy: edges.filter(([from]) => from === name).map(([, to]) => ({solid: {name: to}}))},
    ],
  }));

describe('buildLayout golden layouts', () => {
  it.each(GOLDEN_LAYOUTS)('lays out $name', ({names, edges, waterfall, flat}) => {
    const nodes = nodesFor(names, edges);
    const positions = (mode: GanttChartMode) =>
      buildLayout({nodes, mode}).boxes.map((b) => [b.key, b.x, b.y]);
    expect(positions(GanttChartMode.WATERFALL)).toEqual(waterfall);
    expect(positions(GanttChartMode.FLAT)).toEqual(flat);
  });
});
