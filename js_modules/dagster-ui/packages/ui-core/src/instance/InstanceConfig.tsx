import 'codemirror/addon/search/searchcursor';

import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Code,
  Colors,
  Heading,
  PageHeader,
  Spinner,
  StyledRawCodeMirror,
  Subheading,
} from '@dagster-io/ui-components';
import CodeMirror from 'codemirror';
import {memo, useContext, useMemo} from 'react';
import {createGlobalStyle} from 'styled-components';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {InstanceConfigQuery, InstanceConfigQueryVariables} from './types/InstanceConfig.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

const InstanceConfigStyle = createGlobalStyle`
  .CodeMirror.cm-s-instance-config {
    background-color: ${Colors.backgroundDefault()};
    box-shadow: 0 1px 0 ${Colors.keylineDefault()};
    color: ${Colors.textDefault()};
    height: 100%;
  }

  .CodeMirror.cm-s-instance-config {
    .config-highlight {
      background-color: ${Colors.backgroundLime()};
    }
`;

export const InstanceConfig = memo(() => {
  useTrackPageView();
  useDocumentTitle('Configuration');

  const {pageTitle} = useContext(InstancePageContext);
  const queryResult = useQuery<InstanceConfigQuery, InstanceConfigQueryVariables>(
    INSTANCE_CONFIG_QUERY,
    {
      notifyOnNetworkStatusChange: true,
    },
  );

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;
  const config = data?.instance.info;

  const handlers = useMemo(() => {
    return {
      onReady: (editor: CodeMirror.Editor) => {
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
      },
    };
  }, []);

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
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="config" refreshState={refreshState} />}
      />
      <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
        <Subheading>
          Dagster version: <Code style={{fontSize: '16px'}}>{data.version}</Code>
        </Subheading>
      </Box>
      {/* Div wrapper on CodeMirror to allow entire page to scroll */}
      <div>
        <StyledRawCodeMirror
          value={config || ''}
          options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
          handlers={handlers}
          theme={['instance-config']}
        />
      </div>
    </>
  );
});

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceConfig;

export const INSTANCE_CONFIG_QUERY = gql`
  query InstanceConfigQuery {
    version
    instance {
      id
      info
    }
  }
`;
