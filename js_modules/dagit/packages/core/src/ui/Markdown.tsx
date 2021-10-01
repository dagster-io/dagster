import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import gfm from 'remark-gfm';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

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

const Container = styled.div`
  table tr th {
    color: ${ColorsWIP.Gray400};
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
