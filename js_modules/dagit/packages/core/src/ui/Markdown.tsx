import LRUCache from 'lru-cache';
import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import remark from 'remark';
import gfm from 'remark-gfm';
import toPlainText from 'remark-plain-text';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {FontFamily} from './styles';

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
  &&& table {
    border: none;
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }

  &&& table tr th {
    box-shadow: none !important;
    color: ${ColorsWIP.Gray400};
    font-family: ${FontFamily.default};
    font-size: 12px;
    font-weight: normal;
    padding: 2px 8px;
    text-align: left;
  }

  &&& table tr td {
    box-shadow: none !important;
    padding: 2px 8px;
  }

  &&& table tr th:last-child,
  &&& table tr td:last-child {
    padding-right: 0;
  }
`;
