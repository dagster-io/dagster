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
      const styles = getComputedStyle(measure.current);
      const result = calculateMiddleTruncatedText({width, textString, styles});
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
  width: number;
  styles: CSSStyleDeclaration;
  textString: string;
};

const parsePixels = (value: string) => {
  const parsed = parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

/**
 * Given a font style and a container width, use a canvas to determine the longest possible
 * middle-truncated string that will fit within the container.
 */
const calculateMiddleTruncatedText = ({styles, width, textString}: MeasurementConfig) => {
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

  // Only assign `font` (which carries font-stretch via the shorthand) to the
  // context. Assigning text-shaping properties such as `letterSpacing` or
  // `textRendering` forces the browser off its fast text-measurement path,
  // making each `measureText` call dramatically slower — a cost multiplied by
  // the binary search below and by every rendered row. `letterSpacing` still
  // affects layout width, so we account for it arithmetically instead.
  ctx.font = styles.font;
  const letterSpacing = parsePixels(styles.letterSpacing);
  body.appendChild(canvas);

  // Search for the largest possible middle-truncated string that will fit within
  // the allotted width.
  const truncated = calculateMiddleTruncation(
    textString,
    targetWidth,
    (value: string) =>
      ctx.measureText(value).width + (letterSpacing ? letterSpacing * value.length : 0),
  );

  body.removeChild(canvas);

  return truncated;
};
