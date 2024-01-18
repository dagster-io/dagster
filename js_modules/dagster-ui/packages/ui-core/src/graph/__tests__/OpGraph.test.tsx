import {render, screen} from '@testing-library/react';
import React from 'react';

import * as Common from '../common';
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

describe('OpGraph', () => {
  beforeEach(() => {
    jest.spyOn(Common, 'isNodeOffscreen').mockReturnValue(false);
  });

  it('renders a basic op graph without crashing', async () => {
    const ops = buildBasicDAG();
    render(
      <OpGraph
        jobName="Test Pipeline"
        ops={ops}
        layout={getFullOpLayout(ops, {})}
        interactor={SVGViewport.Interactors.PanAndZoom}
        focusOps={[]}
        highlightedOps={[]}
        onClickOp={() => {}}
      />,
    );
    expect(await screen.getByTestId('A')).toBeVisible();
  });

  it('renders a fan-out op graph', async () => {
    const ops = buildFanOutDAG();
    render(
      <OpGraph
        jobName="Test Pipeline"
        ops={ops}
        layout={getFullOpLayout(ops, {})}
        interactor={SVGViewport.Interactors.PanAndZoom}
        focusOps={[]}
        highlightedOps={[]}
        onClickOp={() => {}}
      />,
    );
    expect(await screen.getByTestId('A')).toBeVisible();
  });

  it('renders an op graph containing tagged ops', async () => {
    const ops = buildTaggedDAG();
    render(
      <OpGraph
        jobName="Test Pipeline"
        ops={ops}
        layout={getFullOpLayout(ops, {})}
        interactor={SVGViewport.Interactors.PanAndZoom}
        focusOps={[]}
        highlightedOps={[]}
        onClickOp={() => {}}
      />,
    );
    expect(await screen.getByTestId('A')).toBeVisible();
  });

  it('renders a basic composite graph - root level', async () => {
    const {ops} = buildCompositeDAG();

    render(
      <OpGraph
        jobName="Test Pipeline"
        ops={ops}
        layout={getFullOpLayout(ops, {})}
        interactor={SVGViewport.Interactors.PanAndZoom}
        focusOps={[]}
        highlightedOps={[]}
        onClickOp={() => {}}
        onEnterSubgraph={() => {}}
        onLeaveSubgraph={() => {}}
        onDoubleClickOp={() => {}}
      />,
    );
    expect(await screen.getByTestId('A')).toBeVisible();
  });

  it('renders a basic composite graph with many IOs - root level', async () => {
    const {ops} = buildCompositeCollapsedIODAG();

    render(
      <OpGraph
        jobName="Test Pipeline"
        ops={ops}
        parentOp={undefined}
        parentHandleID={undefined}
        layout={getFullOpLayout(ops, {})}
        interactor={SVGViewport.Interactors.PanAndZoom}
        focusOps={[]}
        highlightedOps={[]}
        onClickOp={() => {}}
        onEnterSubgraph={() => {}}
        onLeaveSubgraph={() => {}}
        onDoubleClickOp={() => {}}
      />,
    );
    expect(await screen.getByTestId('C')).toBeVisible();
  });

  it('renders a basic composite graph with many IOs - expanded', async () => {
    const {composite: parentOp, childOps} = buildCompositeCollapsedIODAG();

    render(
      <OpGraph
        jobName="Test Pipeline"
        ops={childOps}
        parentOp={parentOp}
        parentHandleID={parentOp.definition.name}
        layout={getFullOpLayout(childOps, {parentOp})}
        interactor={SVGViewport.Interactors.PanAndZoom}
        focusOps={[]}
        highlightedOps={[]}
        onClickOp={() => {}}
        onEnterSubgraph={() => {}}
        onLeaveSubgraph={() => {}}
        onDoubleClickOp={() => {}}
      />,
    );
    expect(await screen.getByTestId('CA')).toBeVisible();
    expect(await screen.getByTestId('CB')).toBeVisible();
  });
});
