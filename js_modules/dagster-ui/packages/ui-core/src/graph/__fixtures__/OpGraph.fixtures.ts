/* eslint-disable @typescript-eslint/no-non-null-assertion */
import {
  buildCompositeSolidDefinition,
  buildInput,
  buildInputDefinition,
  buildInputMapping,
  buildMetadataItemDefinition,
  buildOutput,
  buildOutputDefinition,
  buildOutputMapping,
  buildRegularDagsterType,
  buildSolid,
  buildSolidDefinition,
} from '../../graphql/types';
import {OpGraphOpFragment} from '../types/OpGraph.types';

const IO_TYPE = buildRegularDagsterType({
  displayName: 'Int',
});

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

  return {fromOp: fromOp!, fromIO: fromIO!, toOp: toOp!, toIO: toIO!};
}

function buildGraphSolidFragment(sname: string, ins: string[], outs: string[], edges: Edge[]) {
  const result: OpGraphOpFragment = buildSolid({
    name: sname,
    definition: buildSolidDefinition({
      name: sname,
      description: '',
      metadata: [],
      inputDefinitions: ins.map((iname) =>
        buildInputDefinition({
          name: iname,
          type: IO_TYPE,
        }),
      ),
      outputDefinitions: outs.map((oname) =>
        buildOutputDefinition({
          name: oname,
          type: IO_TYPE,
          isDynamic: false,
        }),
      ),
      configField: null,
      assetNodes: [],
    }),
    inputs: ins.map((iname) =>
      buildInput({
        definition: buildInputDefinition({name: iname}),
        isDynamicCollect: false,
        dependsOn: edges
          .filter((e) => e.toOp === sname && e.toIO === iname)
          .map((o) =>
            buildOutput({
              solid: buildSolid({name: o.fromOp}),
              definition: buildOutputDefinition({name: o.fromIO, type: IO_TYPE}),
            }),
          ),
      }),
    ),
    outputs: outs.map((oname) =>
      buildOutput({
        dependedBy: edges
          .filter((e) => e.fromOp === sname && e.fromIO === oname)
          .map((o) =>
            buildInput({
              solid: buildSolid({name: o.toOp}),
              definition: buildInputDefinition({name: o.toIO, type: IO_TYPE}),
            }),
          ),
        definition: buildOutputDefinition({name: oname}),
      }),
    ),
    isDynamicMapped: false,
  });
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
    ops[idx]!.definition.metadata.push(
      buildMetadataItemDefinition({
        key: 'kind',
        value: kind,
      }),
    ),
  );

  return ops;
}

export function buildCompositeDAG() {
  const ops = buildBasicDAG();

  const composite = ops.find((s) => s.name === 'C')!;

  const edges = [buildEdge(`CA:out=>CB:in`)];
  const childOps = [
    buildGraphSolidFragment(`CA`, ['in'], ['out'], edges),
    buildGraphSolidFragment(`CB`, ['in'], ['out'], edges),
  ];

  composite.definition = buildCompositeSolidDefinition({
    name: composite.definition.name,
    description: composite.definition.description,
    metadata: [],
    assetNodes: [],
    inputDefinitions: composite.definition.inputDefinitions.map((def) =>
      buildInputDefinition({name: def.name, type: IO_TYPE}),
    ),
    outputDefinitions: composite.definition.outputDefinitions.map((def) =>
      buildOutputDefinition({name: def.name, type: IO_TYPE, isDynamic: def.isDynamic}),
    ),
    id: 'composite-solid-id',
    inputMappings: [
      buildInputMapping({
        definition: buildInputDefinition({
          name: composite.definition.inputDefinitions[0]!.name,
        }),
        mappedInput: buildInput({
          solid: buildSolid({name: childOps[0]!.name}),
          definition: buildInputDefinition({
            name: childOps[0]!.definition.inputDefinitions[0]!.name,
          }),
        }),
      }),
    ],
    outputMappings: [
      buildOutputMapping({
        definition: buildOutputDefinition({
          name: composite.definition.outputDefinitions[0]!.name,
        }),
        mappedOutput: buildOutput({
          solid: buildSolid({name: childOps[1]!.name}),
          definition: buildOutputDefinition({
            name: childOps[1]!.definition.outputDefinitions[0]!.name,
          }),
        }),
      }),
    ],
  });
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

  composite.definition = buildCompositeSolidDefinition({
    name: composite.definition.name,
    description: composite.definition.description,
    metadata: [],
    assetNodes: [],
    inputDefinitions: composite.definition.inputDefinitions.map((def) =>
      buildInputDefinition({name: def.name, type: IO_TYPE}),
    ),
    outputDefinitions: composite.definition.outputDefinitions.map((def) =>
      buildOutputDefinition({name: def.name, type: IO_TYPE, isDynamic: def.isDynamic}),
    ),
    id: 'composite-solid-id',
    inputMappings: childOps[0]!.definition.inputDefinitions.map((inputDef, idx) =>
      buildInputMapping({
        definition: buildInputDefinition({
          name: composite.definition.inputDefinitions[idx]!.name,
        }),
        mappedInput: buildInput({
          solid: buildSolid({name: childOps[0]!.name}),
          definition: buildInputDefinition({name: inputDef.name}),
        }),
      }),
    ),
    outputMappings: childOps[1]!.definition.outputDefinitions.map((outputDef, idx) =>
      buildOutputMapping({
        definition: buildOutputDefinition({
          name: composite.definition.outputDefinitions[idx]!.name,
        }),
        mappedOutput: buildOutput({
          solid: buildSolid({name: childOps[1]!.name}),
          definition: buildOutputDefinition({name: outputDef.name}),
        }),
      }),
    ),
  });

  return {ops, composite, childOps};
}
