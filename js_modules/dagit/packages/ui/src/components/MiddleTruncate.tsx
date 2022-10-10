import useResizeObserver from '@react-hook/resize-observer';
import debounce from 'lodash/debounce';
import * as React from 'react';
import styled from 'styled-components/macro';

import {calculateMiddleTruncation} from './calculateMiddleTruncation';

interface Props {
  text: string;
}

const getFont = (element: HTMLDivElement) => getComputedStyle(element).font;

export const MiddleTruncate: React.FC<Props> = (props) => {
  const {text} = props;
  const [targetStyle, setTargetStyle] = React.useState<TargetStyle | null>(null);
  const ref = React.useRef<HTMLDivElement>(null);

  const truncated = useFixedSpan(text, targetStyle);

  // Copy the full text, not just the truncated version shown in the DOM.
  const handleCopy = React.useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      e.preventDefault();
      const clipboardAPI = navigator.clipboard;
      clipboardAPI.writeText(text);
    },
    [text],
  );

  React.useLayoutEffect(() => {
    if (ref.current) {
      const width = ref.current.getBoundingClientRect().width;
      setTargetStyle({font: getFont(ref.current), width});
    }
  }, []);

  const debouncedObserver = React.useMemo(() => {
    return debounce((entry: ResizeObserverEntry) => {
      setTargetStyle((current) => {
        const {width} = entry.contentRect;
        if (current) {
          return {...current, width};
        }
        if (ref.current) {
          return {font: getFont(ref.current), width};
        }
        return null;
      });
    }, 10);
  }, []);

  useResizeObserver(ref.current, debouncedObserver);

  return (
    <MiddleTruncateDiv ref={ref} onCopy={handleCopy} title={text}>
      {truncated}
    </MiddleTruncateDiv>
  );
};

const MiddleTruncateDiv = styled.div`
  overflow: hidden;
  white-space: nowrap;
`;

type TargetStyle = {
  width: number;
  font: string;
};

const useFixedSpan = (text: string, targetStyle: TargetStyle | null) => {
  const [truncated, setTruncated] = React.useState(text);

  React.useEffect(() => {
    if (!targetStyle) {
      return;
    }

    const body = document.body;

    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.left = '-10000px';
    canvas.style.whiteSpace = 'nowrap';
    canvas.style.visibility = 'hidden';

    const ctx = canvas.getContext('2d');

    if (!ctx) {
      return;
    }

    const {width, font} = targetStyle;
    if (!width) {
      return;
    }

    const targetWidth = width;
    ctx.font = font;
    body.appendChild(canvas);

    const truncated = calculateMiddleTruncation(
      text,
      targetWidth,
      (value: string) => ctx.measureText(value).width,
    );

    // If the `end` mark is half the string, we don't need to truncate it.
    setTruncated(truncated);
    body.removeChild(canvas);
  }, [targetStyle, text]);

  return truncated;
};
