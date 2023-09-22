import * as React from 'react';

/**
 * A hook that provides a mechanism for copying a string, triggered by user
 * behavior. If the Clipboard API is available, use it directly.
 *
 * The Clipboard can be undefined in an insecure context
 * (https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API), so we
 * also provide a fallback that uses an offscreen input and `execCommand` to
 * copy the contents. This is less ideal because it steals focus and is a DOM
 * hack, but it should still be effective enough for our needs.
 */
export const useCopyToClipboard = () => {
  const clipboardAPI = navigator.clipboard;
  const node = React.useRef<HTMLInputElement | null>(null);

  React.useEffect(() => {
    if (!clipboardAPI) {
      node.current = document.createElement('input');
      node.current.style.position = 'fixed';
      node.current.style.top = '-10000px';
      document.body.appendChild(node.current);
    }

    return () => {
      node.current && document.body.removeChild(node.current);
    };
  }, [clipboardAPI]);

  return React.useCallback(
    (text: string) => {
      if (clipboardAPI) {
        clipboardAPI.writeText(text);
      } else if (node.current) {
        node.current.value = text;
        node.current.select();
        document.execCommand('copy');
      }
    },
    [clipboardAPI],
  );
};
