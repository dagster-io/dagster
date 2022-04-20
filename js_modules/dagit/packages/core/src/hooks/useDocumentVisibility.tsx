import React from 'react';

// Note: This is a workaround for a problem observed in Firefox - registering
// two visibilitychange event listeners is fine, but if you add a third one
// it is not called reliably (maybe there's an execution time limit before
// the page's JS is paused?)
//
let callbacks: (() => void)[] = [];
document.addEventListener('visibilitychange', () => {
  callbacks.forEach((c) => c());
});

export function useDocumentVisibility() {
  const [documentVisible, setDocumentVisible] = React.useState(
    document.visibilityState !== 'hidden',
  );
  React.useEffect(() => {
    const handler = () => {
      setDocumentVisible(document.visibilityState !== 'hidden');
    };
    callbacks.push(handler);
    return () => {
      callbacks = callbacks.filter((c) => c !== handler);
    };
  });

  return documentVisible;
}
