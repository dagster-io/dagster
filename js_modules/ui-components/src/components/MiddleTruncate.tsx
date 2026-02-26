import useResizeObserver from '@react-hook/resize-observer';
import {
  ClipboardEvent,
  RefObject,
  memo,
  useCallback,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';

import {calculateMiddleTruncation} from './calculateMiddleTruncation';
import styles from './css/MiddleTruncate.module.css';

interface Props {
  // `null` should not happen, but we've seen it sneak through with `!` usage and crash the page,
  // so we'll guard against it.
  text: string | null;
  showTitle?: boolean;
}

const useWidth = (target: RefObject<HTMLDivElement>) => {
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    if (target.current) {
      setWidth(target.current.getBoundingClientRect().width);
    }
  }, [target]);

  useResizeObserver(target, (entry) => setWidth(entry.contentRect.width));
  return width;
};

/**
 * A component that performs middle truncation on a given string, based on the evaluated width
 * of a container div.
 *
 * The component will render the provided string -- with no height/visibility -- into our target
 * container to determine the maximum available width. This width value and the computed font
 * style are then used to determine the longest middle-truncated string that can fit within the width.
 *
 * When the DOM element resizes, the measurement and calculation steps will occur again.
 */
export const MiddleTruncate = memo(({text, showTitle = true}: Props) => {
  const textString = text ?? '';

  // An element that renders the full text into the container, for the purpose of
  // measuring the maximum available/necessary width for our truncated string.
  const measure = useRef<HTMLDivElement>(null);
  const width = useWidth(measure);
  const [truncatedText, setTruncatedText] = useState(textString);

  useLayoutEffect(() => {
    if (measure.current) {
      const font = getComputedStyle(measure.current).font;
      const result = calculateMiddleTruncatedText({font, width, text: textString});
      setTruncatedText(result ?? textString);
    }
  }, [textString, width]);

  // Copy the full text, not just the truncated version shown in the DOM.
  const handleCopy = useCallback(
    (e: ClipboardEvent<HTMLDivElement>) => {
      e.preventDefault();
      const clipboardAPI = navigator.clipboard;
      clipboardAPI.writeText(textString);
    },
    [textString],
  );

  return (
    <div
      className={styles.container}
      onCopy={handleCopy}
      title={showTitle ? textString : undefined}
    >
      <span>{truncatedText}</span>
      <div ref={measure} className={styles.measure}>
        {textString}
      </div>
    </div>
  );
});

type MeasurementConfig = {
  font: string;
  width: number;
  text: string;
};

/**
 * Given a font style and a container width, use a canvas to determine the longest possible
 * middle-truncated string that will fit within the container.
 */
const calculateMiddleTruncatedText = ({font, width, text}: MeasurementConfig) => {
  const body = document.body;

  const canvas = document.createElement('canvas');
  canvas.style.position = 'fixed';
  canvas.style.left = '-10000px';
  canvas.style.whiteSpace = 'nowrap';
  canvas.style.visibility = 'hidden';

  const ctx = canvas.getContext('2d');

  if (!ctx) {
    return null;
  }

  const targetWidth = width;
  ctx.font = font;
  body.appendChild(canvas);

  // Search for the largest possible middle-truncated string that will fit within
  // the allotted width.
  const truncated = calculateMiddleTruncation(
    text,
    targetWidth,
    (value: string) => ctx.measureText(value).width,
  );

  body.removeChild(canvas);

  return truncated;
};
