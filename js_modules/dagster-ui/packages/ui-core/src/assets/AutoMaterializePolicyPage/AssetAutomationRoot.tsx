import {
  Box,
  CursorHistoryControls,
  NonIdealState,
  SpinnerWithText,
} from '@dagster-io/ui-components';
import {useEffect, useRef} from 'react';

import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {AssetKey} from '../types';
import {EvaluationList} from './EvaluationList';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

interface Props {
  assetKey: AssetKey;
  definition: AssetViewDefinitionNodeFragment | null;
}

export const AssetAutomationRoot = ({assetKey, definition}: Props) => {
  const {queryResult, evaluations, paginationProps} = useEvaluationsQueryResult({assetKey});
  const {data, loading} = queryResult;

  const scrollRef = useRef<HTMLDivElement>(null);

  // When paginating, reset scroll to top.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({top: 0, behavior: 'instant'});
    }
  }, [paginationProps.cursor]);

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  if (loading && !data) {
    return (
      <Box padding={64} flex={{direction: 'column', alignItems: 'center'}}>
        <SpinnerWithText label="Loading evaluations…" />
      </Box>
    );
  }

  if (!definition) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="asset"
          title="Asset evaluations not found"
          description="This asset does not have any automation evaluations."
        />
      </Box>
    );
  }

  return (
    <>
      <Box
        padding={{vertical: 12, horizontal: 20}}
        flex={{direction: 'row', justifyContent: 'flex-end'}}
      >
        <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} />
      </Box>
      <div style={{overflowY: 'auto'}} ref={scrollRef}>
        <EvaluationList
          evaluations={evaluations}
          assetKey={assetKey}
          isPartitioned={definition.partitionDefinition !== null}
        />
      </div>
    </>
  );
};
