import {act, render, renderHook} from '@testing-library/react';
import React from 'react';

import {AssetGraphLayout} from '../layout';
import {useAssetGroupViewportAnchor} from '../useAssetGroupViewportAnchor';

type Viewport = {
  getScale: jest.Mock<number, []>;
  shiftXY: jest.Mock<void, [number, number]>;
};

const group = (id: string, expanded: boolean) => ({
  id,
  groupName: id,
  repositoryName: 'repo',
  repositoryLocationName: 'location',
  bounds: {x: 0, y: 0, width: 100, height: 50},
  expanded,
  depth: id.split('/').length - 1,
});

const layout = (groups: Record<string, boolean>): AssetGraphLayout => ({
  width: 500,
  height: 500,
  edges: [],
  nodes: {},
  groups: Object.fromEntries(
    Object.entries(groups).map(([id, expanded]) => [id, group(id, expanded)]),
  ),
});

const foreignObjectAt = (left: number, top: number) => {
  const element = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
  jest.spyOn(element, 'getBoundingClientRect').mockReturnValue({
    x: left,
    y: top,
    left,
    top,
    right: left + 100,
    bottom: top + 50,
    width: 100,
    height: 50,
    toJSON: () => ({}),
  });
  return element;
};

const viewportAtScale = (scale: number): Viewport => ({
  getScale: jest.fn(() => scale),
  shiftXY: jest.fn(),
});

const rectAt = (left: number, top: number) => ({
  x: left,
  y: top,
  left,
  top,
  right: left + 100,
  bottom: top + 50,
  width: 100,
  height: 50,
  toJSON: () => ({}),
});

type AnchorHarnessProps = {
  currentLayout: AssetGraphLayout;
  expandedGroups: string[];
  viewportRef: {current: Viewport};
  anchorKey: string;
  anchorPosition: {left: number; top: number};
  onAnchorElement: (element: SVGForeignObjectElement) => void;
  onAnchorReady: (anchor: ReturnType<typeof useAssetGroupViewportAnchor>) => void;
  onAfterLayoutEffect: () => void;
};

const AnchorNode = ({
  currentLayout,
  expandedGroups,
  viewportRef,
  anchorKey,
  anchorPosition,
  onAnchorElement,
  onAnchorReady,
}: Omit<AnchorHarnessProps, 'onAfterLayoutEffect'>) => {
  const anchor = useAssetGroupViewportAnchor({
    layout: currentLayout,
    expandedGroups,
    viewportRef,
  });
  const groupRef = anchor.anchorRefForGroup('parent');
  const ref = React.useCallback(
    (element: SVGForeignObjectElement | null) => {
      groupRef(element);
      if (element) {
        jest
          .spyOn(element, 'getBoundingClientRect')
          .mockReturnValue(rectAt(anchorPosition.left, anchorPosition.top));
        onAnchorElement(element);
      }
    },
    [anchorPosition.left, anchorPosition.top, groupRef, onAnchorElement],
  );

  React.useLayoutEffect(() => {
    onAnchorReady(anchor);
  }, [anchor, onAnchorReady]);

  return (
    <svg>
      <foreignObject data-testid="group-anchor" key={anchorKey} ref={ref} />
    </svg>
  );
};

const LayoutEffectObserver = ({
  layout,
  onObserve,
}: {
  layout: AssetGraphLayout;
  onObserve: () => void;
}) => {
  React.useLayoutEffect(() => {
    onObserve();
  }, [layout, onObserve]);
  return null;
};

const AnchorHarness = ({onAfterLayoutEffect, ...anchorNodeProps}: AnchorHarnessProps) => (
  <>
    <AnchorNode {...anchorNodeProps} />
    <LayoutEffectObserver layout={anchorNodeProps.currentLayout} onObserve={onAfterLayoutEffect} />
  </>
);

describe('useAssetGroupViewportAnchor', () => {
  it.each([
    {
      name: 'expansion',
      initiallyExpanded: [] as string[],
      expectedExpanded: true,
      before: {left: -120, top: 80},
      after: {left: -165, top: 50},
      scale: 0.75,
      shift: [45, 30],
    },
    {
      name: 'collapse',
      initiallyExpanded: ['parent'],
      expectedExpanded: false,
      before: {left: 240, top: -130},
      after: {left: 280, top: -100},
      scale: 1.4,
      shift: [-40, -30],
    },
  ])(
    'anchors a $name without changing the $scale viewport scale',
    ({initiallyExpanded, expectedExpanded, before, after, scale, shift}) => {
      const sourceLayout = layout({parent: !expectedExpanded});
      const targetLayout = layout({parent: expectedExpanded});
      const viewport = viewportAtScale(scale);
      const ref = {current: viewport};
      const {result, rerender} = renderHook(
        ({currentLayout, expandedGroups}) =>
          useAssetGroupViewportAnchor({layout: currentLayout, expandedGroups, viewportRef: ref}),
        {initialProps: {currentLayout: sourceLayout, expandedGroups: initiallyExpanded}},
      );
      const anchor = foreignObjectAt(before.left, before.top);

      act(() => {
        result.current.anchorRefForGroup('parent')(anchor);
        result.current.captureBeforeToggle('parent', expectedExpanded);
      });

      jest.spyOn(anchor, 'getBoundingClientRect').mockReturnValue({
        x: after.left,
        y: after.top,
        left: after.left,
        top: after.top,
        right: after.left + 100,
        bottom: after.top + 50,
        width: 100,
        height: 50,
        toJSON: () => ({}),
      });
      rerender({
        currentLayout: targetLayout,
        expandedGroups: expectedExpanded ? ['parent'] : [],
      });

      expect(viewport.shiftXY).toHaveBeenCalledTimes(1);
      expect(viewport.shiftXY).toHaveBeenCalledWith(...shift);
      expect(viewport.getScale()).toBe(scale);
      expect(result.current.consumeHandledLayout(targetLayout)).toBe(true);
      expect(result.current.consumeHandledLayout(targetLayout)).toBe(false);
    },
  );

  it('uses the remounted SVG anchor before later layout effects observe the matching layout', () => {
    const sourceLayout = layout({parent: false});
    const targetLayout = layout({parent: true});
    const viewport = viewportAtScale(1);
    const viewportRef = {current: viewport};
    const elements: SVGForeignObjectElement[] = [];
    const layoutEffectShiftCounts: number[] = [];
    let anchor: ReturnType<typeof useAssetGroupViewportAnchor> | undefined;
    const onAnchorElement = jest.fn((element: SVGForeignObjectElement) => elements.push(element));
    const onAnchorReady = jest.fn((nextAnchor: ReturnType<typeof useAssetGroupViewportAnchor>) => {
      anchor = nextAnchor;
    });
    const onAfterLayoutEffect = jest.fn(() => {
      layoutEffectShiftCounts.push(viewport.shiftXY.mock.calls.length);
    });
    const {rerender} = render(
      <AnchorHarness
        currentLayout={sourceLayout}
        expandedGroups={[]}
        viewportRef={viewportRef}
        anchorKey="before"
        anchorPosition={{left: 100, top: 200}}
        onAnchorElement={onAnchorElement}
        onAnchorReady={onAnchorReady}
        onAfterLayoutEffect={onAfterLayoutEffect}
      />,
    );
    const firstAnchorRef = anchor?.anchorRefForGroup('parent');

    act(() => {
      anchor?.captureBeforeToggle('parent', true);
    });
    const detachedElement = elements[0];
    if (!detachedElement) {
      throw new Error('Expected the initial anchor element');
    }
    jest.spyOn(detachedElement, 'getBoundingClientRect').mockImplementation(() => {
      throw new Error('A detached anchor must not be measured');
    });
    rerender(
      <AnchorHarness
        currentLayout={targetLayout}
        expandedGroups={['parent']}
        viewportRef={viewportRef}
        anchorKey="after"
        anchorPosition={{left: 70, top: 250}}
        onAnchorElement={onAnchorElement}
        onAnchorReady={onAnchorReady}
        onAfterLayoutEffect={onAfterLayoutEffect}
      />,
    );

    expect(elements).toHaveLength(2);
    expect(elements[1]).not.toBe(elements[0]);
    expect(anchor?.anchorRefForGroup('parent')).toBe(firstAnchorRef);
    expect(viewport.shiftXY).toHaveBeenCalledWith(30, -50);
    expect(layoutEffectShiftCounts).toEqual([0, 1]);
  });

  it('marks only the direct nested target as pending', () => {
    const sourceLayout = layout({parent: true, 'parent/child': false});
    const viewport = viewportAtScale(1);
    const {result} = renderHook(() =>
      useAssetGroupViewportAnchor({
        layout: sourceLayout,
        expandedGroups: ['parent'],
        viewportRef: {current: viewport},
      }),
    );

    act(() => {
      result.current.anchorRefForGroup('parent/child')(foreignObjectAt(30, 40));
      result.current.captureBeforeToggle('parent/child', true);
    });

    expect(result.current.isPendingGroup('parent')).toBe(false);
    expect(result.current.isPendingGroup('parent/child')).toBe(true);
  });

  it('waits through an intermediate layout whose group state does not match the toggle', () => {
    const sourceLayout = layout({parent: false});
    const intermediateLayout = layout({parent: false});
    const targetLayout = layout({parent: true});
    const viewport = viewportAtScale(1);
    const ref = {current: viewport};
    const {result, rerender} = renderHook(
      ({currentLayout, expandedGroups}) =>
        useAssetGroupViewportAnchor({layout: currentLayout, expandedGroups, viewportRef: ref}),
      {initialProps: {currentLayout: sourceLayout, expandedGroups: [] as string[]}},
    );
    const anchor = foreignObjectAt(100, 200);

    act(() => {
      result.current.anchorRefForGroup('parent')(anchor);
      result.current.captureBeforeToggle('parent', true);
    });
    rerender({currentLayout: intermediateLayout, expandedGroups: ['parent']});

    expect(viewport.shiftXY).not.toHaveBeenCalled();
    expect(result.current.isPendingGroup('parent')).toBe(true);

    jest.spyOn(anchor, 'getBoundingClientRect').mockReturnValue({
      x: 70,
      y: 250,
      left: 70,
      top: 250,
      right: 170,
      bottom: 300,
      width: 100,
      height: 50,
      toJSON: () => ({}),
    });
    rerender({currentLayout: targetLayout, expandedGroups: ['parent']});

    expect(viewport.shiftXY).toHaveBeenCalledTimes(1);
    expect(viewport.shiftXY).toHaveBeenCalledWith(30, -50);
  });

  it('lets a newer nested toggle supersede a parent toggle', () => {
    const sourceLayout = layout({parent: false, 'parent/child': false});
    const oldTargetLayout = layout({parent: true, 'parent/child': false});
    const targetLayout = layout({parent: true, 'parent/child': true});
    const viewport = viewportAtScale(1);
    const ref = {current: viewport};
    const {result, rerender} = renderHook(
      ({currentLayout, expandedGroups}) =>
        useAssetGroupViewportAnchor({layout: currentLayout, expandedGroups, viewportRef: ref}),
      {initialProps: {currentLayout: sourceLayout, expandedGroups: [] as string[]}},
    );
    const parent = foreignObjectAt(20, 30);
    const child = foreignObjectAt(-40, 90);

    act(() => {
      result.current.anchorRefForGroup('parent')(parent);
      result.current.captureBeforeToggle('parent', true);
      result.current.anchorRefForGroup('parent/child')(child);
      result.current.captureBeforeToggle('parent/child', true);
    });
    rerender({currentLayout: oldTargetLayout, expandedGroups: ['parent', 'parent/child']});

    expect(viewport.shiftXY).not.toHaveBeenCalled();
    expect(result.current.isPendingGroup('parent/child')).toBe(true);

    jest.spyOn(child, 'getBoundingClientRect').mockReturnValue({
      x: -70,
      y: 60,
      left: -70,
      top: 60,
      right: 30,
      bottom: 110,
      width: 100,
      height: 50,
      toJSON: () => ({}),
    });
    rerender({currentLayout: targetLayout, expandedGroups: ['parent', 'parent/child']});

    expect(viewport.shiftXY).toHaveBeenCalledTimes(1);
    expect(viewport.shiftXY).toHaveBeenCalledWith(30, 30);
  });

  it('finishes without shifting when the target group is missing from the next layout', () => {
    const sourceLayout = layout({parent: false});
    const targetLayout = layout({});
    const viewport = viewportAtScale(1);
    const ref = {current: viewport};
    const {result, rerender} = renderHook(
      ({currentLayout, expandedGroups}) =>
        useAssetGroupViewportAnchor({layout: currentLayout, expandedGroups, viewportRef: ref}),
      {initialProps: {currentLayout: sourceLayout, expandedGroups: [] as string[]}},
    );

    act(() => {
      result.current.anchorRefForGroup('parent')(foreignObjectAt(10, 10));
      result.current.captureBeforeToggle('parent', true);
    });
    rerender({currentLayout: targetLayout, expandedGroups: ['parent']});

    expect(viewport.shiftXY).not.toHaveBeenCalled();
    expect(result.current.isPendingGroup('parent')).toBe(false);
    expect(result.current.consumeHandledLayout(targetLayout)).toBe(true);
    expect(result.current.consumeHandledLayout(targetLayout)).toBe(false);
  });

  it('preserves a newer viewport zoom instead of applying a stale anchor shift', () => {
    const sourceLayout = layout({parent: false});
    const targetLayout = layout({parent: true});
    const viewport = viewportAtScale(0.75);
    const ref = {current: viewport};
    const {result, rerender} = renderHook(
      ({currentLayout, expandedGroups}) =>
        useAssetGroupViewportAnchor({layout: currentLayout, expandedGroups, viewportRef: ref}),
      {initialProps: {currentLayout: sourceLayout, expandedGroups: [] as string[]}},
    );

    act(() => {
      result.current.anchorRefForGroup('parent')(foreignObjectAt(10, 10));
      result.current.captureBeforeToggle('parent', true);
    });
    viewport.getScale.mockReturnValue(1.4);
    rerender({currentLayout: targetLayout, expandedGroups: ['parent']});

    expect(viewport.shiftXY).not.toHaveBeenCalled();
    expect(result.current.isPendingGroup('parent')).toBe(false);
    expect(result.current.consumeHandledLayout(targetLayout)).toBe(true);
    expect(result.current.consumeHandledLayout(targetLayout)).toBe(false);
  });

  it('cancels when the desired expanded state no longer matches the direct toggle', () => {
    const sourceLayout = layout({parent: false});
    const cancelledLayout = layout({parent: true});
    const viewport = viewportAtScale(1);
    const ref = {current: viewport};
    const {result, rerender} = renderHook(
      ({currentLayout, expandedGroups}) =>
        useAssetGroupViewportAnchor({layout: currentLayout, expandedGroups, viewportRef: ref}),
      {initialProps: {currentLayout: sourceLayout, expandedGroups: [] as string[]}},
    );

    act(() => {
      result.current.anchorRefForGroup('parent')(foreignObjectAt(10, 10));
      result.current.captureBeforeToggle('parent', true);
    });
    rerender({currentLayout: cancelledLayout, expandedGroups: []});

    expect(viewport.shiftXY).not.toHaveBeenCalled();
    expect(result.current.isPendingGroup('parent')).toBe(false);
    expect(result.current.consumeHandledLayout(cancelledLayout)).toBe(true);
    expect(result.current.consumeHandledLayout(cancelledLayout)).toBe(false);
  });

  it('ignores unrelated layouts when no direct toggle transaction is pending', () => {
    const currentLayout = layout({parent: false});
    const unrelatedLayout = layout({unrelated: true});
    const viewport = viewportAtScale(1);
    const {result, rerender} = renderHook(
      ({currentLayout}) =>
        useAssetGroupViewportAnchor({
          layout: currentLayout,
          expandedGroups: [],
          viewportRef: {current: viewport},
        }),
      {initialProps: {currentLayout}},
    );

    rerender({currentLayout: unrelatedLayout});

    expect(viewport.shiftXY).not.toHaveBeenCalled();
    expect(result.current.isPendingGroup('parent')).toBe(false);
    expect(result.current.consumeHandledLayout(unrelatedLayout)).toBe(false);
  });
});
