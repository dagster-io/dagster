import {Meta} from '@storybook/react';
import {useState} from 'react';

import {OpNameOrPath} from '../../ops/OpNameOrPath';
import {OpGraph} from '../OpGraph';
import {SVGViewport} from '../SVGViewport';
import {
  buildBasicDAG,
  buildCompositeCollapsedIODAG,
  buildCompositeDAG,
  buildFanOutDAG,
  buildTaggedDAG,
} from '../__fixtures__/OpGraph.fixtures';
import {getFullOpLayout} from '../asyncGraphLayout';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'OpGraph',
  component: OpGraph,
} as Meta;

export const Basic = () => {
  const [focusOps, setsetFocusOps] = useState<string[]>([]);
  const ops = buildBasicDAG();

  return (
    <OpGraph
      jobName="Test Pipeline"
      ops={ops}
      layout={getFullOpLayout(ops, {})}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(s) => setsetFocusOps(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const FanOut = () => {
  const [focusOps, setsetFocusOps] = useState<string[]>([]);

  const ops = buildFanOutDAG();
  return (
    <OpGraph
      jobName="Test Pipeline"
      ops={ops}
      layout={getFullOpLayout(ops, {})}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(s) => setsetFocusOps(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const Tagged = () => {
  const [focusOps, setsetFocusOps] = useState<string[]>([]);
  const ops = buildTaggedDAG();
  return (
    <OpGraph
      jobName="Test Pipeline"
      ops={ops}
      layout={getFullOpLayout(ops, {})}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(s) => setsetFocusOps(['name' in s ? s.name : s.path.join('.')])}
    />
  );
};

export const Composite = () => {
  const [focusOps, setFocusOps] = useState<string[]>([]);
  const [parentOpName, setParentOpName] = useState<string | undefined>();

  const toName = (s: OpNameOrPath) => ('name' in s ? s.name : s.path.join('.'));
  const {ops, childOps} = buildCompositeDAG();
  const parentOp = ops.find((s) => s.name === parentOpName);

  return (
    <OpGraph
      jobName="Test Pipeline"
      ops={parentOp ? childOps : ops}
      parentOp={parentOp}
      parentHandleID={parentOpName}
      layout={parentOp ? getFullOpLayout(childOps, {parentOp}) : getFullOpLayout(ops, {})}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(nameOrPath) => setFocusOps([toName(nameOrPath)])}
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

export const CompositeCollapsedIO = () => {
  const [focusOps, setFocusOps] = useState<string[]>([]);
  const [parentOpName, setParentOpName] = useState<string | undefined>();

  const toName = (s: OpNameOrPath) => ('name' in s ? s.name : s.path.join('.'));

  const {ops, childOps} = buildCompositeCollapsedIODAG();
  const parentOp = ops.find((s) => s.name === parentOpName);

  return (
    <OpGraph
      jobName="Test Pipeline"
      ops={parentOp ? childOps : ops}
      parentOp={parentOp}
      parentHandleID={parentOpName}
      layout={parentOp ? getFullOpLayout(childOps, {parentOp}) : getFullOpLayout(ops, {})}
      interactor={SVGViewport.Interactors.PanAndZoom}
      focusOps={ops.filter((s) => focusOps.includes(s.name))}
      highlightedOps={[]}
      onClickOp={(nameOrPath) => setFocusOps([toName(nameOrPath)])}
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
