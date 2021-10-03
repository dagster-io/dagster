import {Colors} from '@blueprintjs/core';
import LRUCache from 'lru-cache';
import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import remark from 'remark';
import gfm from 'remark-gfm';
import toPlainText from 'remark-plain-text';
import styled from 'styled-components/macro';

interface Props {
  children: string;
}

export const Markdown: React.FC<Props> = (props) => {
  return (
    <Container>
      <ReactMarkdown remarkPlugins={[gfm]} {...props} />
    </Container>
  );
};

const Remark = remark()
  .use(gfm)
  .use(toPlainText as any);
const markdownCache = new LRUCache<string, string>({max: 500});
export const markdownToPlaintext = (md: string) => {
  // Compile the Markdown file to plain text:
  const cached = markdownCache.get(md);
  if (cached) {
    return cached;
  }
  const str = Remark.processSync(md).toString();
  markdownCache.set(md, str);
  return str;
};

const Container = styled.div`
  table tr th {
    color: ${Colors.GRAY3};
    font-weight: normal;
    padding: 4px 16px 4px 0;
    text-align: left;
  }

  table tr td {
    padding: 2px 16px 2px 0;
  }

  table tr th:last-child,
  table tr td:last-child {
    padding-right: 0;
  }
`;
