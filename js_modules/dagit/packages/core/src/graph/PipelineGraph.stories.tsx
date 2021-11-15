import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {OpNameOrPath} from '../ops/OpNameOrPath';
import {ColorsWIP} from '../ui/Colors';

import {PipelineGraph} from './PipelineGraph';
import {SVGViewport} from './SVGViewport';
import {getDagrePipelineLayout} from './getFullOpLayout';
import {PipelineGraphOpFragment} from './types/PipelineGraphOpFragment';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'PipelineGraph',
  component: PipelineGraph,
} as Meta;

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
  return {fromOp, fromIO, toOp, toIO};
}

function buildGraphSolidFragment(sname: string, ins: string[], outs: string[], edges: Edge[]) {
  const result: PipelineGraphOpFragment = {
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

function buildBasicDAG() {
  const edges = ['A:out=>B:in', 'B:out1=>C:in', 'B:out2=>D:in1', 'C:out=>D:in2'].map(buildEdge);

  const ops: PipelineGraphOpFragment[] = [
    buildGraphSolidFragment('A', [], ['out'], edges),
    buildGraphSolidFragment('B', ['in'], ['out1', 'out2'], edges),
    buildGraphSolidFragment('C', ['in'], ['out'], edges),
    buildGraphSolidFragment('D', ['in1', 'in2'], [], edges),
  ];
  return ops;
}

export const Basic = () => {
  const [focusOps, setsetFocusOps] = React.useState<string[]>([]);
  const ops = buildBasicDAG();

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      ops={ops}
      layout={getDagrePipelineLayout(ops)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(s) => setsetFocusOps(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const FanOut = () => {
  const [focusOps, setsetFocusOps] = React.useState<string[]>([]);

  const edges = [];
  for (let ii = 0; ii < 60; ii++) {
    edges.push(buildEdge(`A:out=>B${ii}:in`));
    edges.push(buildEdge(`B${ii}:out=>C:in`));
  }
  const ops: PipelineGraphOpFragment[] = [];
  ops.push(buildGraphSolidFragment('A', ['in'], ['out'], edges));
  ops.push(buildGraphSolidFragment('C', ['in'], ['out'], edges));
  for (let ii = 0; ii < 60; ii++) {
    ops.push(buildGraphSolidFragment(`B${ii}`, ['in'], ['out'], edges));
  }

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      ops={ops}
      layout={getDagrePipelineLayout(ops)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(s) => setsetFocusOps(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const Tagged = () => {
  const [focusOps, setsetFocusOps] = React.useState<string[]>([]);
  const ops = buildBasicDAG();

  ['ipynb', 'sql', 'verylongtypename', 'story'].forEach((kind, idx) =>
    ops[idx].definition.metadata.push({
      key: 'kind',
      value: kind,
      __typename: 'MetadataItemDefinition',
    }),
  );

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      ops={ops}
      layout={getDagrePipelineLayout(ops)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(s) => setsetFocusOps(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const Composite = () => {
  const [focusOps, setsetFocusOps] = React.useState<string[]>([]);
  const [parentOpName, setParentOpName] = React.useState<string | undefined>();
  const ops = buildBasicDAG();
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
        definition: composite.definition.inputDefinitions[0],
        mappedInput: {
          __typename: 'Input',
          solid: childOps[0],
          definition: childOps[0].definition.inputDefinitions[0],
        },
      },
    ],
    outputMappings: [
      {
        __typename: 'OutputMapping',
        definition: composite.definition.outputDefinitions[0],
        mappedOutput: {
          __typename: 'Output',
          solid: childOps[1],
          definition: childOps[1].definition.outputDefinitions[0],
        },
      },
    ],
  };

  const toName = (s: OpNameOrPath) => ('name' in s ? s.name : s.path.join('.'));
  const parentOp = ops.find((s) => s.name === parentOpName);

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      ops={parentOp ? childOps : ops}
      parentOp={parentOp}
      parentHandleID={parentOpName}
      layout={parentOp ? getDagrePipelineLayout(childOps, parentOp) : getDagrePipelineLayout(ops)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(nameOrPath) => setsetFocusOps([toName(nameOrPath)])}
      onEnterSubgraph={(nameOrPath) => setParentOpName(toName(nameOrPath))}
      onLeaveSubgraph={() => setParentOpName(undefined)}
      onDoubleClickOp={(nameOrPath) => {
        const solid = ops.find((s) => s.name === toName(nameOrPath));
        if (solid?.definition.__typename === 'CompositeSolidDefinition') {
          setParentOpName(solid.name);
        }
      }}
    />
  );
};
