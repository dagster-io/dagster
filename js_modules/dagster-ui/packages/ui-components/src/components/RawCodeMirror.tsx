import 'codemirror/lib/codemirror.css';

import CodeMirror from 'codemirror';
import * as React from 'react';

type CodeMirrorHandlers = {
  onReady?: (instance: CodeMirror.Editor) => void;
  onChange?: (instance: CodeMirror.Editor) => void;
  onBlur?: (instance: CodeMirror.Editor) => void;
  onCursorActivity?: (instance: CodeMirror.Editor) => void;
  onKeyUp?: (instance: CodeMirror.Editor, event: Event) => void;
};

const REFRESH_DELAY_MSEC = 200;

interface Props {
  value: string;
  options?: CodeMirror.EditorConfiguration;
  handlers?: CodeMirrorHandlers;
}

export const RawCodeMirror = (props: Props) => {
  const {value, options, handlers} = props;
  const cm = React.useRef<CodeMirror.EditorFromTextArea | null>(null);

  React.useEffect(() => {
    if (value !== cm.current?.getValue()) {
      cm.current?.setValue(value);
    }
  }, [value]);

  const ref = React.useCallback(
    (node: HTMLTextAreaElement | null) => {
      if (!node) {
        return;
      }

      if (cm.current) {
        return;
      }

      cm.current = CodeMirror.fromTextArea(node, {
        value,
        ...options,
      });

      // Wait a moment for the DOM to settle, then call refresh to ensure that all
      // CSS has finished loading. This allows CodeMirror to correctly align elements,
      // including the cursor.
      setTimeout(() => {
        cm.current?.refresh();
      }, REFRESH_DELAY_MSEC);

      if (!handlers) {
        return;
      }

      if (handlers.onChange) {
        cm.current.on('change', handlers.onChange);
      }

      if (handlers.onBlur) {
        cm.current.on('blur', handlers.onBlur);
      }

      if (handlers.onCursorActivity) {
        cm.current.on('cursorActivity', handlers.onCursorActivity);
      }

      if (handlers.onKeyUp) {
        cm.current.on('keyup', handlers.onKeyUp);
      }

      if (handlers.onReady) {
        handlers.onReady(cm.current);
      }
    },
    [value, options, handlers],
  );

  React.useEffect(() => {
    // Check current options and update if necessary.
    if (cm.current && options) {
      Object.entries(options).forEach(([key, value]) => {
        const castKey = key as keyof CodeMirror.EditorConfiguration;
        if (cm.current?.getOption(castKey) !== value) {
          cm.current?.setOption(castKey, value);
        }
      });
    }
  }, [options]);

  return <textarea ref={ref} />;
};
