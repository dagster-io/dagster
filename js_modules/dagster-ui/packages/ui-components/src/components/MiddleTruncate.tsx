import useResizeObserver from '@react-hook/resize-observer';
import * as React from 'react';
import styled from 'styled-components';

import {calculateMiddleTruncation} from './calculateMiddleTruncation';

interface Props {
  text: string;
  showTitle?: boolean;
}

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
export const MiddleTruncate = React.memo(({text, showTitle = true}: Props) => {
  // An element that renders the full text into the container, for the purpose of
  // measuring the maximum available/necessary width for our truncated string.
  const measure = React.useRef<HTMLDivElement>(null);
  const truncated = React.useRef<HTMLDivElement>(null);

  // Given the target font style and allotted width, calculate the largest possible middle-
  // truncated string.
  const calculateTargetStyle = React.useCallback(() => {
    if (measure.current && truncated.current) {
      truncated.current.textContent = calculateMiddleTruncatedText(measure.current, text);
    }
  }, [text]);

  // Use a layout effect to trigger the process of calculating the truncated text, for the
  // initial render.
  React.useLayoutEffect(() => {
    window.requestAnimationFrame(calculateTargetStyle);
  }, [calculateTargetStyle]);

  // If the container has just been resized, recalculate.
  useResizeObserver(measure.current, () => {
    calculateTargetStyle();
  });

  // Copy the full text, not just the truncated version shown in the DOM.
  const handleCopy = React.useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      e.preventDefault();
      const clipboardAPI = navigator.clipboard;
      clipboardAPI.writeText(text);
    },
    [text],
  );

  return (
    <Container onCopy={handleCopy} title={showTitle ? text : undefined}>
      <span ref={truncated}></span>
      <MeasureWidth ref={measure}>{text}</MeasureWidth>
    </Container>
  );
});

// An invisible target element that contains the full, no-wrapped text. This is used
// to measure the maximum available width for our truncated string.
const MeasureWidth = styled.div`
  height: 0;
  overflow: hidden;
  white-space: nowrap;
`;

const Container = styled.div`
  overflow: hidden;
  white-space: nowrap;
`;

/**
 * Compute the font style and maximum/necessary width for the measured container,
 * for the specified string of text.
 *
 * Given those values, use a 2D canvas context to determine the longest possible
 * middle-truncated string.
 */
const calculateMiddleTruncatedText = (container: HTMLDivElement, text: string) => {
  const font = getComputedStyle(container).font;

  // https://developer.mozilla.org/en-US/docs/Web/API/CSS_Object_Model/Determining_the_dimensions_of_elements#how_much_room_does_it_use_up
  const width = container.offsetWidth;

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
