import throttle from 'lodash/throttle';
import {MouseEvent as ReactMouseEvent, useCallback, useEffect, useRef, useState} from 'react';

import {AssetGraphLayout} from './layout';
import {SVGViewportRef} from '../graph/SVGViewport';
import {IPoint} from '../graph/common';

const DRAG_THRESHOLD_PX = 5;

export interface UseNodeDragOptions {
  layout: AssetGraphLayout | null;
  viewportRef: React.MutableRefObject<SVGViewportRef | undefined>;
  onCommitPosition: (nodeId: string, position: IPoint) => void;
  onCommitMultiplePositions: (updates: Record<string, IPoint>) => void;
}

export interface UseNodeDragResult {
  onNodeMouseDown: (nodeId: string, e: ReactMouseEvent) => void;
  onGroupMouseDown: (groupId: string, childNodeIds: string[], e: ReactMouseEvent) => void;
  draggingNodeId: string | null;
  /** Ephemeral positions for ALL nodes currently being dragged (single node or group children). */
  draggedNodePositions: Record<string, IPoint>;
}

export function useNodeDrag({
  layout,
  viewportRef,
  onCommitPosition,
  onCommitMultiplePositions,
}: UseNodeDragOptions): UseNodeDragResult {
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [draggedNodePositions, setDraggedNodePositions] = useState<Record<string, IPoint>>({});

  // Refs to active document listeners so we can clean them up on unmount
  const activeListenersRef = useRef<Array<() => void>>([]);

  useEffect(() => {
    return () => {
      // Remove any document listeners still attached (e.g. component unmounted mid-drag)
      // Only remove listeners — skip setState since the component is unmounting
      for (const cleanup of activeListenersRef.current) {
        cleanup();
      }
      activeListenersRef.current = [];
    };
  }, []);

  const createDragSession = useCallback(
    (e: ReactMouseEvent, onMove: (delta: IPoint) => void, onUp: (delta: IPoint) => void) => {
      if (e.button !== 0) {
        return;
      }
      e.stopPropagation();

      const viewport = viewportRef.current;
      if (!viewport || !layout) {
        return;
      }

      const startScreen = viewport.getOffsetXY(e);
      if (!startScreen) {
        return;
      }

      document.body.style.cursor = 'grabbing';

      const startSVG = viewport.screenToSVGCoords(startScreen);
      let didDrag = false;
      // Track the last known good delta so mouseup can fall back to it
      // if getOffsetXY returns null (e.g. mouse released outside the browser window).
      let lastDelta: IPoint = {x: 0, y: 0};

      // Capture reduced-motion preference once per drag session
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      const onMouseMove = throttle((moveEvent: MouseEvent) => {
        const vp = viewportRef.current;
        if (!vp) {
          return;
        }
        const offset = vp.getOffsetXY(moveEvent);
        if (!offset) {
          return;
        }
        const svgPos = vp.screenToSVGCoords(offset);

        if (!didDrag) {
          const screenDx = offset.x - startScreen.x;
          const screenDy = offset.y - startScreen.y;
          if (Math.sqrt(screenDx * screenDx + screenDy * screenDy) < DRAG_THRESHOLD_PX) {
            return;
          }
        }

        didDrag = true;
        lastDelta = {x: svgPos.x - startSVG.x, y: svgPos.y - startSVG.y};
        // Skip live drag preview when the user prefers reduced motion; position
        // is still committed on mouseup via onUp.
        if (!prefersReducedMotion) {
          onMove(lastDelta);
        }
      }, 1000 / 60);

      const onCancelClick = (clickEvent: MouseEvent) => {
        if (didDrag) {
          clickEvent.stopImmediatePropagation();
          clickEvent.preventDefault();
        }
      };

      const onMouseUp = (upEvent: MouseEvent) => {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        onMouseMove.cancel();
        // Defer click-listener removal to suppress the click event that follows mouseup.
        // Keep removeListeners in activeListenersRef until after the timeout fires so
        // that an unmount in this window still cleans up onCancelClick correctly.
        setTimeout(() => {
          document.removeEventListener('click', onCancelClick, {capture: true});
          activeListenersRef.current = activeListenersRef.current.filter(
            (fn) => fn !== removeListeners,
          );
        });

        if (didDrag) {
          const vp = viewportRef.current;
          if (vp) {
            const offset = vp.getOffsetXY(upEvent);
            // Fall back to lastDelta if getOffsetXY returns null (e.g. mouse released
            // outside the browser window or viewport element removed during a fast navigation).
            const delta = offset
              ? {
                  x: vp.screenToSVGCoords(offset).x - startSVG.x,
                  y: vp.screenToSVGCoords(offset).y - startSVG.y,
                }
              : lastDelta;
            onUp(delta);
          }
        }

        document.body.style.cursor = '';
        setDraggingNodeId(null);
        setDraggedNodePositions({});
      };

      const removeListeners = () => {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.removeEventListener('click', onCancelClick, {capture: true});
        onMouseMove.cancel();
      };

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
      document.addEventListener('click', onCancelClick, {capture: true});
      activeListenersRef.current.push(removeListeners);
    },
    [layout, viewportRef],
  );

  const onNodeMouseDown = useCallback(
    (nodeId: string, e: ReactMouseEvent) => {
      const nodeLayout = layout?.nodes[nodeId];
      if (!nodeLayout) {
        return;
      }
      const startPos: IPoint = {x: nodeLayout.bounds.x, y: nodeLayout.bounds.y};

      createDragSession(
        e,
        (delta) => {
          setDraggingNodeId(nodeId);
          setDraggedNodePositions({[nodeId]: {x: startPos.x + delta.x, y: startPos.y + delta.y}});
        },
        (delta) => {
          onCommitPosition(nodeId, {x: startPos.x + delta.x, y: startPos.y + delta.y});
        },
      );
    },
    [layout, createDragSession, onCommitPosition],
  );

  const onGroupMouseDown = useCallback(
    (groupId: string, childNodeIds: string[], e: ReactMouseEvent) => {
      const groupLayout = layout?.groups[groupId];
      if (!groupLayout) {
        return;
      }

      if (!groupLayout.expanded) {
        // Collapsed group — drag using group bounds directly
        const startPos: IPoint = {x: groupLayout.bounds.x, y: groupLayout.bounds.y};
        createDragSession(
          e,
          (delta) => {
            setDraggingNodeId(groupId);
            setDraggedNodePositions({
              [groupId]: {x: startPos.x + delta.x, y: startPos.y + delta.y},
            });
          },
          (delta) => {
            onCommitPosition(groupId, {x: startPos.x + delta.x, y: startPos.y + delta.y});
          },
        );
        return;
      }

      // Expanded group — drag all children together
      const groupStartPos: IPoint = {x: groupLayout.bounds.x, y: groupLayout.bounds.y};
      const childStartPositions: Record<string, IPoint> = {};
      for (const childId of childNodeIds) {
        const childLayout = layout.nodes[childId];
        if (childLayout) {
          childStartPositions[childId] = {x: childLayout.bounds.x, y: childLayout.bounds.y};
        }
      }

      createDragSession(
        e,
        (delta) => {
          setDraggingNodeId(groupId);
          const positions: Record<string, IPoint> = {};
          for (const [childId, startPos] of Object.entries(childStartPositions)) {
            positions[childId] = {x: startPos.x + delta.x, y: startPos.y + delta.y};
          }
          setDraggedNodePositions(positions);
        },
        (delta) => {
          const updates: Record<string, IPoint> = {
            // Also save the group's own position so collapsing after a drag
            // uses the overridden position instead of the original Dagre bounds.
            [groupId]: {x: groupStartPos.x + delta.x, y: groupStartPos.y + delta.y},
          };
          for (const [childId, startPos] of Object.entries(childStartPositions)) {
            updates[childId] = {x: startPos.x + delta.x, y: startPos.y + delta.y};
          }
          onCommitMultiplePositions(updates);
        },
      );
    },
    [layout, createDragSession, onCommitPosition, onCommitMultiplePositions],
  );

  return {onNodeMouseDown, onGroupMouseDown, draggingNodeId, draggedNodePositions};
}
