import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import gfm from 'remark-gfm';
import styled from 'styled-components/macro';

import {Colors} from './Colors';
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

const Container = styled.div`
  &&& table {
    border: none;
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }

  &&& table tr th {
    box-shadow: none !important;
    color: ${Colors.Gray400};
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
