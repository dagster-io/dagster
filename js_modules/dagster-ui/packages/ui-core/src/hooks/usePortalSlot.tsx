import React from 'react';
import {createPortal} from 'react-dom';

/**
 * Allows you to move a component around in the tree without it losing its state.
 */
export function usePortalSlot(reactNode: React.ReactNode) {
  const [targetEl, setTargetEl] = React.useState<HTMLDivElement | null>(null);

  React.useLayoutEffect(() => {
    setTargetEl((e) => (e === null ? document.createElement('div') : e));
  }, []);

  return [
    targetEl ? createPortal(reactNode, targetEl) : null,
    targetEl ? <DOMNodeHost node={targetEl} /> : null,
  ];
}

function DOMNodeHost({node}: {node: HTMLElement}) {
  const ref = React.useRef<HTMLDivElement | null>(null);
  React.useLayoutEffect(() => {
    const ownDiv = ref.current;
    if (node.parentNode === ownDiv) {
      return;
    }
    if (node.parentNode !== null && node.parentNode !== ownDiv) {
      throw Error('Cannot render the same node twice');
    }
    ownDiv?.appendChild(node);
    return () => {
      ownDiv?.removeChild(node);
    };
  }, [node]);
  return <div ref={ref} />;
}
