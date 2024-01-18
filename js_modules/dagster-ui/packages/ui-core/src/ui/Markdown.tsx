import * as React from 'react';
import styled from 'styled-components';

import {FontFamily, colorTextLight} from '@dagster-io/ui-components';

const MarkdownWithPlugins = React.lazy(() => import('./MarkdownWithPlugins'));

interface Props {
  children: string;
}

export const Markdown = (props: Props) => {
  return (
    <Container>
      <React.Suspense fallback={<div />}>
        <MarkdownWithPlugins {...props} />
      </React.Suspense>
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
    color: ${colorTextLight()};
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
