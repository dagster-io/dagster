import {Spinner} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {UnControlled as CodeMirrorReact} from 'react-codemirror2';
import styled from 'styled-components/macro';
import {createGlobalStyle} from 'styled-components/macro';

import {Header} from 'src/ListComponents';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {InstanceDetailsQuery} from 'src/types/InstanceDetailsQuery';
import {FontFamily} from 'src/ui/styles';

const CodeMirrorShimStyle = createGlobalStyle`
  .react-codemirror2 {
    height: 100%;
    flex: 1;
    position: relative;
  }
  .react-codemirror2 .CodeMirror {
    font-family: ${FontFamily.monospace};
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    height: initial;
  }
`;

export const InstanceDetailsRoot: React.FunctionComponent = () => {
  useDocumentTitle('Instance Details');
  const {data} = useQuery<InstanceDetailsQuery>(INSTANCE_DETAILS_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return data ? (
    <Container>
      <TopNav breadcrumbs={[{text: 'Instance Details', icon: 'database'}]} />
      <div style={{flexGrow: 1, padding: '16px 16px 32px'}}>
        <Header>{`Dagster ${data.version}`}</Header>
        <CodeMirrorShimStyle />
        <CodeMirrorReact
          value={data?.instance.info}
          options={{
            mode: 'yaml',
            readOnly: true,
          }}
        />
      </div>
    </Container>
  ) : (
    <Spinner size={35} />
  );
};

const Container = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
`;

export const INSTANCE_DETAILS_QUERY = gql`
  query InstanceDetailsQuery {
    version
    instance {
      info
    }
  }
`;
