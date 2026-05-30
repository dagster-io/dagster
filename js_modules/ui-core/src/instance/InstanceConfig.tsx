import 'codemirror/addon/search/searchcursor';

import {Box, Code, PageHeader, Spinner, Subheading, Subtitle1} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import CodeMirror from 'codemirror';
import {memo, useContext, useMemo} from 'react';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {gql, useQuery} from '../apollo-client';
import styles from './css/InstanceConfig.module.css';
import {InstanceConfigQuery, InstanceConfigQueryVariables} from './types/InstanceConfig.types';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const InstanceConfigContent = memo(() => {
  useTrackPageView();
  useDocumentTitle('Configuration');

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
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border="bottom"
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>
          Dagster version: <Code style={{fontSize: '16px'}}>{data.version}</Code>
        </Subheading>
        <QueryRefreshCountdown refreshState={refreshState} />
      </Box>
      {/* Div wrapper on CodeMirror to allow entire page to scroll */}
      <div className={styles.configEditor} style={{flex: 1, overflow: 'hidden'}}>
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

export const InstanceConfigRoot = () => {
  const {pageTitle} = useContext(InstancePageContext);
  return (
    <>
      <PageHeader title={<Subtitle1>{pageTitle}</Subtitle1>} tabs={<InstanceTabs tab="config" />} />
      <InstanceConfigContent />
    </>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceConfigRoot;

export const INSTANCE_CONFIG_QUERY = gql`
  query InstanceConfigQuery {
    version
    instance {
      id
      info
    }
  }
`;
