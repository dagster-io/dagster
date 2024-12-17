import {Button} from '@dagster-io/ui-components';
import useResizeObserver from '@react-hook/resize-observer';
import * as React from 'react';
import styled from 'styled-components';

import {Markdown} from '../ui/Markdown';

interface IDescriptionProps {
  description: string | null;
  maxHeight?: number;
  fontSize?: string | number;
}

const DEFAULT_MAX_HEIGHT = 320;

/*
If `input` begins with whitespace and every line contains at least that whitespace,
it removes it. Otherwise, return the original string.
*/
function removeLeadingSpaces(input: string) {
  const leadingSpaces = /^\n?( +)/.exec(input);
  if (leadingSpaces == null) {
    return input;
  }

  const lines = input.split('\n');
  if (!lines.every((l) => l.substr(0, leadingSpaces[1]!.length).trim() === '')) {
    return input;
  }

  return lines.map((l) => l.substr(leadingSpaces[1]!.length)).join('\n');
}

export const Description = ({maxHeight, description, fontSize}: IDescriptionProps) => {
  const container = React.createRef<HTMLDivElement>();
  const [hasMore, setHasMore] = React.useState(false);
  const [expanded, setExpanded] = React.useState(false);

  const updateHasMore = React.useCallback(() => {
    if (!container.current) {
      return;
    }
    setHasMore(container.current.clientHeight > (maxHeight || DEFAULT_MAX_HEIGHT));
  }, [container, maxHeight]);

  // On mount, recalculate whether to show "show more"
  React.useLayoutEffect(updateHasMore, [updateHasMore]);

  // If the container has been resized, recalculate.
  useResizeObserver(container.current, updateHasMore);

  // If the content has changed, recalculate. This is necessary because our Markdown
  // support is lazy-loaded and seems to take one React render to populate after it loads,
  // and also means you can change the `description` prop.
  React.useLayoutEffect(() => {
    if (!container.current || !('MutationObserver' in window)) {
      return;
    }
    const mutationObserver = new MutationObserver(updateHasMore);
    mutationObserver.observe(container.current, {subtree: true, childList: true});
    return () => mutationObserver.disconnect();
  }, [container, updateHasMore]);

  if (!description || description.length === 0) {
    return null;
  }

  return (
    <Container
      onDoubleClick={() => {
        const sel = document.getSelection();
        if (!sel || !container.current) {
          return;
        }
        const range = document.createRange();
        range.selectNodeContents(container.current);
        sel.removeAllRanges();
        sel.addRange(range);
      }}
      $fontSize={fontSize || '0.8rem'}
      style={{
        maxHeight: expanded ? undefined : maxHeight || DEFAULT_MAX_HEIGHT,
      }}
    >
      {hasMore && (
        <ShowMoreHandle>
          <Button intent="primary" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Show less' : 'Show more'}
          </Button>
        </ShowMoreHandle>
      )}

      <div ref={container} style={{overflowX: 'auto'}}>
        <Markdown>{removeLeadingSpaces(description)}</Markdown>
      </div>
    </Container>
  );
};

const Container = styled.div<{$fontSize: string | number}>`
  overflow: hidden;
  position: relative;
  font-size: ${({$fontSize}) => (typeof $fontSize === 'number' ? `${$fontSize}px` : $fontSize)};
  p:last-child {
    margin-bottom: 0;
  }

  & code,
  & pre {
    font-size: ${({$fontSize}) => (typeof $fontSize === 'number' ? `${$fontSize}px` : $fontSize)};
  }
`;

const ShowMoreHandle = styled.div`
  position: absolute;
  padding: 0 14px;
  bottom: 0;
  left: 50%;
  transform: translate(-50%);
`;
