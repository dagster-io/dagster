import 'codemirror/addon/search/searchcursor';

import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Colors,
  DagitReadOnlyCodeMirror,
  PageHeader,
  Spinner,
  Code,
  Heading,
  Subheading,
} from '@dagster-io/ui';
import * as codemirror from 'codemirror';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';

import {InstanceTabs} from './InstanceTabs';
import {InstanceConfigQuery} from './types/InstanceConfigQuery';

const InstanceConfigStyle = createGlobalStyle`
  .react-codemirror2 .CodeMirror.cm-s-instance-config {
    box-shadow: 0 1px 0 ${Colors.KeylineGray};
    height: 100%;
  }

  .react-codemirror2 .CodeMirror.cm-s-instance-config {
    .config-highlight {
      background-color: ${Colors.Yellow200};
    }
`;

export const InstanceConfig = React.memo(() => {
  const queryResult = useQuery<InstanceConfigQuery>(INSTANCE_CONFIG_QUERY, {
    fetchPolicy: 'cache-and-network',
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;
  const config = data?.instance.info;

  const onEditorDidMount = (editor: codemirror.Editor) => {
    const documentHash = document.location.hash;
    if (documentHash) {
      const target = new RegExp(`^${documentHash.slice(1)}:`);
      const cursor = editor.getSearchCursor(target);
      const found = cursor.findNext();
      if (found) {
        editor.markText(cursor.from(), cursor.to(), {className: 'config-highlight'});
        editor.scrollIntoView(cursor.from());
      }
    }
  };

  if (!data) {
    return (
      <Box padding={{vertical: 64}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  return (
    <>
      <InstanceConfigStyle />
      <PageHeader
        title={<Heading>Instance status</Heading>}
        tabs={<InstanceTabs tab="config" refreshState={refreshState} />}
      />
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Subheading>
          Dagster version: <Code style={{fontSize: '16px'}}>{data.version}</Code>
        </Subheading>
      </Box>
      <DagitReadOnlyCodeMirror
        editorDidMount={onEditorDidMount}
        value={config || ''}
        options={{lineNumbers: true, mode: 'yaml'}}
        theme={['instance-config']}
      />
    </>
  );
});

export const INSTANCE_CONFIG_QUERY = gql`
  query InstanceConfigQuery {
    version
    instance {
      info
    }
  }
`;
