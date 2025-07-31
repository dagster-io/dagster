import {OpGraphOpFragment} from '../types/OpGraph.types';

const IO_TYPE = {
  __typename: 'RegularDagsterType',
  displayName: 'Int',
} as const;

interface Edge {
  fromOp: string;
  fromIO: string;
  toOp: string;
  toIO: string;
}

function buildEdge(descriptor: string): Edge {
  const match = /([\w\d.]*):([\w\d.]*) ?=> ?([\w\d.]*):([\w\d.]*)/g.exec(descriptor);
  if (!match) {
    throw new Error(`Cannot parse ${descriptor}`);
  }
  const [_, fromOp, fromIO, toOp, toIO] = match;
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return {fromOp: fromOp!, fromIO: fromIO!, toOp: toOp!, toIO: toIO!};
}

function buildGraphSolidFragment(sname: string, ins: string[], outs: string[], edges: Edge[]) {
  const result: OpGraphOpFragment = {
    __typename: 'Solid',
    name: sname,
    definition: {
      __typename: 'SolidDefinition',
      name: sname,
      description: '',
      metadata: [],
      inputDefinitions: ins.map((iname) => ({
        __typename: 'InputDefinition',
        name: iname,
        type: IO_TYPE,
      })),
      outputDefinitions: outs.map((oname) => ({
        __typename: 'OutputDefinition',
        name: oname,
        type: IO_TYPE,
        isDynamic: false,
      })),
      configField: null,
      assetNodes: [],
    },
    inputs: ins.map((iname) => ({
      __typename: 'Input',
      definition: {__typename: 'InputDefinition', name: iname},
      isDynamicCollect: false,
      dependsOn: edges
        .filter((e) => e.toOp === sname && e.toIO === iname)
        .map((o) => ({
          __typename: 'Output',
          solid: {name: o.fromOp, __typename: 'Solid'},
          definition: {__typename: 'OutputDefinition', name: o.fromIO, type: IO_TYPE},
        })),
    })),
    outputs: outs.map((oname) => ({
      __typename: 'Output',
      dependedBy: edges
        .filter((e) => e.fromOp === sname && e.fromIO === oname)
        .map((o) => ({
          __typename: 'Input',
          solid: {name: o.toOp, __typename: 'Solid'},
          definition: {__typename: 'InputDefinition', name: o.toIO, type: IO_TYPE},
        })),
      definition: {__typename: 'OutputDefinition', name: oname},
    })),
    isDynamicMapped: false,
  };
  return result;
}

export function buildBasicDAG() {
  const edges = ['A:out=>B:in', 'B:out1=>C:in', 'B:out2=>D:in1', 'C:out=>D:in2'].map(buildEdge);

  const ops: OpGraphOpFragment[] = [
    buildGraphSolidFragment('A', [], ['out'], edges),
    buildGraphSolidFragment('B', ['in'], ['out1', 'out2'], edges),
    buildGraphSolidFragment('C', ['in'], ['out'], edges),
    buildGraphSolidFragment('D', ['in1', 'in2'], [], edges),
  ];
  return ops;
}

export function buildFanOutDAG() {
  const edges = [];
  for (let ii = 0; ii < 60; ii++) {
    edges.push(buildEdge(`A:out=>B${ii}:in`));
    edges.push(buildEdge(`B${ii}:out=>C:in`));
  }
  const ops: OpGraphOpFragment[] = [];
  ops.push(buildGraphSolidFragment('A', ['in'], ['out'], edges));
  ops.push(buildGraphSolidFragment('C', ['in'], ['out'], edges));
  for (let ii = 0; ii < 60; ii++) {
    ops.push(buildGraphSolidFragment(`B${ii}`, ['in'], ['out'], edges));
  }
  return ops;
}

export function buildTaggedDAG() {
  const ops = buildBasicDAG();

  ['ipynb', 'sql', 'verylongtypename', 'story'].forEach((kind, idx) =>
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    ops[idx]!.definition.metadata.push({
      key: 'kind',
      value: kind,
      __typename: 'MetadataItemDefinition',
    }),
  );

  return ops;
}

export function buildCompositeDAG() {
  const ops = buildBasicDAG();
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const composite = ops.find((s) => s.name === 'C')!;

  const edges = [buildEdge(`CA:out=>CB:in`)];
  const childOps = [
    buildGraphSolidFragment(`CA`, ['in'], ['out'], edges),
    buildGraphSolidFragment(`CB`, ['in'], ['out'], edges),
  ];

  composite.definition = {
    ...composite.definition,
    __typename: 'CompositeSolidDefinition',
    id: 'composite-solid-id',
    inputMappings: [
      {
        __typename: 'InputMapping',
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        definition: composite.definition.inputDefinitions[0]!,
        mappedInput: {
          __typename: 'Input',
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          solid: childOps[0]!,
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          definition: childOps[0]!.definition.inputDefinitions[0]!,
        },
      },
    ],
    outputMappings: [
      {
        __typename: 'OutputMapping',
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        definition: composite.definition.outputDefinitions[0]!,
        mappedOutput: {
          __typename: 'Output',
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          solid: childOps[1]!,
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          definition: childOps[1]!.definition.outputDefinitions[0]!,
        },
      },
    ],
  };
  return {ops, composite, childOps};
}

export function buildCompositeCollapsedIODAG() {
  const composite = buildGraphSolidFragment(
    'C',
    ['in1', 'in2', 'in3', 'in4', 'in5'],
    ['out1', 'out2', 'out3', 'out4', 'out5'],
    [],
  );
  const ops: OpGraphOpFragment[] = [composite];

  const childEdges = [buildEdge(`CA:out=>CB:in`)];
  const childOps = [
    buildGraphSolidFragment(`CA`, ['in1', 'in2', 'in3', 'in4', 'in5'], ['out'], childEdges),
    buildGraphSolidFragment(`CB`, ['in'], ['out1', 'out2', 'out3', 'out4', 'out5'], childEdges),
  ];

  composite.definition = {
    ...composite.definition,
    __typename: 'CompositeSolidDefinition',
    id: 'composite-solid-id',
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    inputMappings: childOps[0]!.definition.inputDefinitions.map((inputDef, idx) => ({
      __typename: 'InputMapping',
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      definition: composite.definition.inputDefinitions[idx]!,
      mappedInput: {
        __typename: 'Input',
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        solid: childOps[0]!,
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        definition: inputDef!,
      },
    })),
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    outputMappings: childOps[1]!.definition.outputDefinitions.map((outputDef, idx) => ({
      __typename: 'OutputMapping',
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      definition: composite.definition.outputDefinitions[idx]!,
      mappedOutput: {
        __typename: 'Output',
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        solid: childOps[1]!,
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        definition: outputDef!,
      },
    })),
  };

  return {ops, composite, childOps};
}
