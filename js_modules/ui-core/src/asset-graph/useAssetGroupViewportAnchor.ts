import * as React from 'react';

import {AssetGraphLayout} from './layout';
import {SVGViewportRef} from '../graph/SVGViewport';

type ViewportRef = Readonly<{
  current: Pick<SVGViewportRef, 'getScale' | 'shiftXY'> | undefined;
}>;

type UseAssetGroupViewportAnchorOptions = {
  layout: AssetGraphLayout | null;
  expandedGroups: string[];
  viewportRef: ViewportRef;
};

type PendingAnchor = {
  sourceLayout: AssetGraphLayout;
  groupId: string;
  expectedExpanded: boolean;
  point: {left: number; top: number} | undefined;
  scale: number | undefined;
};

export const useAssetGroupViewportAnchor = ({
  layout,
  expandedGroups,
  viewportRef,
}: UseAssetGroupViewportAnchorOptions) => {
  const anchorElementsRef = React.useRef(new Map<string, SVGForeignObjectElement>());
  const anchorCallbacksRef = React.useRef(
    new Map<string, React.RefCallback<SVGForeignObjectElement>>(),
  );
  const pendingRef = React.useRef<PendingAnchor | undefined>();
  const handledLayoutsRef = React.useRef(new WeakSet<AssetGraphLayout>());

  const anchorRefForGroup = React.useCallback((groupId: string) => {
    const existing = anchorCallbacksRef.current.get(groupId);
    if (existing) {
      return existing;
    }

    const callback: React.RefCallback<SVGForeignObjectElement> = (element) => {
      if (element) {
        anchorElementsRef.current.set(groupId, element);
      } else {
        anchorElementsRef.current.delete(groupId);
      }
    };
    anchorCallbacksRef.current.set(groupId, callback);
    return callback;
  }, []);

  const captureBeforeToggle = React.useCallback(
    (groupId: string, expectedExpanded: boolean) => {
      if (!layout) {
        return;
      }

      const element = anchorElementsRef.current.get(groupId);
      const rect = element?.getBoundingClientRect();
      const viewport = viewportRef.current;
      pendingRef.current = {
        sourceLayout: layout,
        groupId,
        expectedExpanded,
        point: rect ? {left: rect.left, top: rect.top} : undefined,
        scale: viewport?.getScale(),
      };
    },
    [layout, viewportRef],
  );

  const consumeHandledLayout = React.useCallback((handledLayout: AssetGraphLayout | null) => {
    if (!handledLayout || !handledLayoutsRef.current.has(handledLayout)) {
      return false;
    }
    handledLayoutsRef.current.delete(handledLayout);
    return true;
  }, []);

  const isPendingGroup = React.useCallback((groupId: string) => {
    return pendingRef.current?.groupId === groupId;
  }, []);

  React.useLayoutEffect(() => {
    const pending = pendingRef.current;
    if (!pending || !layout || layout === pending.sourceLayout) {
      return;
    }

    const finish = () => {
      handledLayoutsRef.current.add(layout);
      pendingRef.current = undefined;
    };

    if (expandedGroups.includes(pending.groupId) !== pending.expectedExpanded) {
      finish();
      return;
    }

    const targetGroup = layout.groups[pending.groupId];
    if (!targetGroup) {
      finish();
      return;
    }
    if (targetGroup.expanded !== pending.expectedExpanded) {
      return;
    }

    const viewport = viewportRef.current;
    const element = anchorElementsRef.current.get(pending.groupId);
    const after = element?.getBoundingClientRect();
    if (!viewport || !pending.point || pending.scale === undefined || !after) {
      finish();
      return;
    }

    if (viewport.getScale() !== pending.scale) {
      finish();
      return;
    }

    finish();
    viewport.shiftXY(pending.point.left - after.left, pending.point.top - after.top);
  }, [expandedGroups, layout, viewportRef]);

  return {
    anchorRefForGroup,
    captureBeforeToggle,
    consumeHandledLayout,
    isPendingGroup,
  };
};
