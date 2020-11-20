import {gql, useQuery} from '@apollo/client';
import {Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {UnControlled as CodeMirrorReact} from 'react-codemirror2';
import {createGlobalStyle} from 'styled-components/macro';

import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {InstanceDetailsQuery} from 'src/instance/types/InstanceDetailsQuery';
import {Box} from 'src/ui/Box';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Subheading} from 'src/ui/Text';
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
  useDocumentTitle('Instance details');
  const {data} = useQuery<InstanceDetailsQuery>(INSTANCE_DETAILS_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return data ? (
    <div style={{display: 'flex', flexDirection: 'column', height: '100%'}}>
      <Page style={{flexGrow: 1}}>
        <PageHeader text="Instance details" />
        <Box margin={{bottom: 12}}>
          <Subheading>{`Dagster ${data.version}`}</Subheading>
        </Box>
        <CodeMirrorShimStyle />
        <CodeMirrorReact
          value={data?.instance.info}
          options={{
            mode: 'yaml',
            readOnly: true,
          }}
        />
      </Page>
    </div>
  ) : (
    <Spinner size={35} />
  );
};

export const INSTANCE_DETAILS_QUERY = gql`
  query InstanceDetailsQuery {
    version
    instance {
      info
    }
  }
`;
