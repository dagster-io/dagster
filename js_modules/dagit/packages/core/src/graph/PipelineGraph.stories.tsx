import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {ColorsWIP} from '../ui/Colors';

import {PipelineGraph} from './PipelineGraph';
import {SVGViewport} from './SVGViewport';
import {getDagrePipelineLayout} from './getFullSolidLayout';
import {PipelineGraphSolidFragment} from './types/PipelineGraphSolidFragment';

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
  fromSolid: string;
  fromIO: string;
  toSolid: string;
  toIO: string;
}

function buildEdge(descriptor: string): Edge {
  const match = /([\w\d.]*):([\w\d.]*) ?=> ?([\w\d.]*):([\w\d.]*)/g.exec(descriptor);
  if (!match) {
    throw new Error(`Cannot parse ${descriptor}`);
  }
  const [_, fromSolid, fromIO, toSolid, toIO] = match;
  return {fromSolid, fromIO, toSolid, toIO};
}

function buildGraphSolidFragment(sname: string, ins: string[], outs: string[], edges: Edge[]) {
  const result: PipelineGraphSolidFragment = {
    __typename: 'Solid',
    name: sname,
    definition: {
      __typename: 'SolidDefinition',
      name: sname,
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
        .filter((e) => e.toSolid === sname && e.toIO === iname)
        .map((o) => ({
          __typename: 'Output',
          solid: {name: o.fromSolid, __typename: 'Solid'},
          definition: {__typename: 'OutputDefinition', name: o.fromIO, type: IO_TYPE},
        })),
    })),
    outputs: outs.map((oname) => ({
      __typename: 'Output',
      dependedBy: edges
        .filter((e) => e.fromSolid === sname && e.fromIO === oname)
        .map((o) => ({
          __typename: 'Input',
          solid: {name: o.toSolid, __typename: 'Solid'},
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

  const solids: PipelineGraphSolidFragment[] = [
    buildGraphSolidFragment('A', [], ['out'], edges),
    buildGraphSolidFragment('B', ['in'], ['out1', 'out2'], edges),
    buildGraphSolidFragment('C', ['in'], ['out'], edges),
    buildGraphSolidFragment('D', ['in1', 'in2'], [], edges),
  ];
  return solids;
}

export const Basic = () => {
  const [focusSolids, setFocusSolids] = React.useState<string[]>([]);
  const solids = buildBasicDAG();

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      solids={solids}
      layout={getDagrePipelineLayout(solids)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusSolids={solids.filter((s) => focusSolids.includes(s.name))}
      highlightedSolids={[]}
      onClickSolid={(s) => setFocusSolids(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const FanOut = () => {
  const [focusSolids, setFocusSolids] = React.useState<string[]>([]);

  const edges = [];
  for (let ii = 0; ii < 60; ii++) {
    edges.push(buildEdge(`A:out=>B${ii}:in`));
    edges.push(buildEdge(`B${ii}:out=>C:in`));
  }
  const solids: PipelineGraphSolidFragment[] = [];
  solids.push(buildGraphSolidFragment('A', ['in'], ['out'], edges));
  solids.push(buildGraphSolidFragment('C', ['in'], ['out'], edges));
  for (let ii = 0; ii < 60; ii++) {
    solids.push(buildGraphSolidFragment(`B${ii}`, ['in'], ['out'], edges));
  }

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      solids={solids}
      layout={getDagrePipelineLayout(solids)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusSolids={solids.filter((s) => focusSolids.includes(s.name))}
      highlightedSolids={[]}
      onClickSolid={(s) => setFocusSolids(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const Tagged = () => {
  const [focusSolids, setFocusSolids] = React.useState<string[]>([]);
  const solids = buildBasicDAG();

  ['ipynb', 'sql', 'verylongtypename', 'story'].forEach((kind, idx) =>
    solids[idx].definition.metadata.push({
      key: 'kind',
      value: kind,
      __typename: 'MetadataItemDefinition',
    }),
  );

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      solids={solids}
      layout={getDagrePipelineLayout(solids)}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusSolids={solids.filter((s) => focusSolids.includes(s.name))}
      highlightedSolids={[]}
      onClickSolid={(s) => setFocusSolids(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const Composite = () => {
  const [focusSolids, setFocusSolids] = React.useState<string[]>([]);
  const [parentSolidName, setParentSolidName] = React.useState<string | undefined>();
  const solids = buildBasicDAG();
  const composite = solids.find((s) => s.name === 'C')!;

  const edges = [buildEdge(`CA:out=>CB:in`)];
  const childSolids = [
    buildGraphSolidFragment(`CA`, ['in'], ['out'], edges),
    buildGraphSolidFragment(`CB`, ['in'], ['out'], edges),
  ];

  composite.definition = {
    ...composite.definition,
    __typename: 'CompositeSolidDefinition',
    inputMappings: [
      {
        __typename: 'InputMapping',
        definition: composite.definition.inputDefinitions[0],
        mappedInput: {
          __typename: 'Input',
          solid: childSolids[0],
          definition: childSolids[0].definition.inputDefinitions[0],
        },
      },
    ],
    outputMappings: [
      {
        __typename: 'OutputMapping',
        definition: composite.definition.outputDefinitions[0],
        mappedOutput: {
          __typename: 'Output',
          solid: childSolids[1],
          definition: childSolids[1].definition.outputDefinitions[0],
        },
      },
    ],
  };

  const toName = (s: SolidNameOrPath) => ('name' in s ? s.name : s.path.join('.'));
  const parentSolid = solids.find((s) => s.name === parentSolidName);

  return (
    <PipelineGraph
      backgroundColor={ColorsWIP.White}
      pipelineName={'Test Pipeline'}
      solids={parentSolid ? childSolids : solids}
      parentSolid={parentSolid}
      parentHandleID={parentSolidName}
      layout={
        parentSolid
          ? getDagrePipelineLayout(childSolids, parentSolid)
          : getDagrePipelineLayout(solids)
      }
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusSolids={solids.filter((s) => focusSolids.includes(s.name))}
      highlightedSolids={[]}
      onClickSolid={(nameOrPath) => setFocusSolids([toName(nameOrPath)])}
      onEnterCompositeSolid={(nameOrPath) => setParentSolidName(toName(nameOrPath))}
      onLeaveCompositeSolid={() => setParentSolidName(undefined)}
      onDoubleClickSolid={(nameOrPath) => {
        const solid = solids.find((s) => s.name === toName(nameOrPath));
        if (solid?.definition.__typename === 'CompositeSolidDefinition') {
          setParentSolidName(solid.name);
        }
      }}
    />
  );
};
