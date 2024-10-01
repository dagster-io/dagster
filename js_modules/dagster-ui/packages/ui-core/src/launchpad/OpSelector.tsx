import {Box, Colors, Popover} from '@dagster-io/ui-components';
import {useRef, useState} from 'react';
import styled from 'styled-components';

import {OpSelectorQuery, OpSelectorQueryVariables} from './types/OpSelector.types';
import {gql, useQuery} from '../apollo-client';
import {filterByQuery} from '../app/GraphQueryImpl';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {explodeCompositesInHandleGraph} from '../pipelines/CompositeSupport';
import {GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/GraphExplorer';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface IOpSelectorProps {
  pipelineName: string;
  serverProvidedSubsetError?: {message: string};
  value: string[] | null;
  query: string | null;
  onChange: (value: string[] | null, query: string | null) => void;
  flattenGraphs: boolean;
  onFlattenGraphsChange: (v: boolean) => void;
  repoAddress: RepoAddress;
}

const SOLID_SELECTOR_QUERY = gql`
  query OpSelectorQuery($selector: PipelineSelector!, $requestScopeHandleID: String) {
    pipelineOrError(params: $selector) {
      ... on Pipeline {
        id
        name
        solidHandles(parentHandleID: $requestScopeHandleID) {
          handleID
          solid {
            name
          }
          ...GraphExplorerSolidHandleFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const OpSelector = (props: IOpSelectorProps) => {
  const {serverProvidedSubsetError, onChange, pipelineName, repoAddress, onFlattenGraphsChange} =
    props;
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const flattenGraphs = props.flattenGraphs || false;
  const selector = {...repoAddressToSelector(repoAddress), pipelineName};
  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);
  const {data, loading} = useQuery<OpSelectorQuery, OpSelectorQueryVariables>(
    SOLID_SELECTOR_QUERY,
    {
      variables: {selector, requestScopeHandleID: flattenGraphs ? undefined : ''},
    },
  );

  const query = props.query || '*';

  const opHandles =
    data?.pipelineOrError.__typename === 'Pipeline'
      ? flattenGraphs
        ? explodeCompositesInHandleGraph(data.pipelineOrError.solidHandles)
        : data.pipelineOrError.solidHandles
      : [];
  const ops = opHandles.map((h) => h.solid);
  const flattenGraphsEnabled =
    flattenGraphs || ops.some((f) => f.definition.__typename === 'CompositeSolidDefinition');

  const opsFetchError =
    (data?.pipelineOrError.__typename !== 'Pipeline' && data?.pipelineOrError.message) || null;

  const queryResultOps = filterByQuery(ops, query).all;
  const invalidOpSelection = !loading && queryResultOps.length === 0;

  const errorMessage = invalidOpSelection
    ? isJob
      ? `You must provide a valid op query or * to execute the entire job.`
      : `You must provide a valid solid query or * to execute the entire pipeline.`
    : serverProvidedSubsetError
    ? serverProvidedSubsetError.message
    : opsFetchError;

  const onTextChange = (nextQuery: string) => {
    if (nextQuery === '') {
      nextQuery = '*';
    }
    const queryResultOps = filterByQuery(ops, nextQuery).all;

    // If all ops are returned, we set the subset to null rather than sending
    // a comma separated list of evey solid to the API
    if (queryResultOps.length === ops.length) {
      onChange(null, nextQuery);
    } else {
      onChange(
        queryResultOps.map((s) => s.name),
        nextQuery,
      );
    }
  };

  if (!data?.pipelineOrError) {
    return null;
  }

  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Popover
        isOpen={focused && !!errorMessage}
        position="bottom-left"
        content={<PopoverErrorWrap>{errorMessage}</PopoverErrorWrap>}
      >
        <ShortcutHandler
          shortcutLabel="⌥S"
          shortcutFilter={(e) => e.code === 'KeyS' && e.altKey}
          onShortcut={() => inputRef.current?.focus()}
        >
          <GraphQueryInput
            width={(query !== '*' && query !== '') || focused || flattenGraphsEnabled ? 350 : 90}
            intent={errorMessage ? 'danger' : 'none'}
            items={ops}
            ref={inputRef}
            value={query}
            placeholder="Type an op subset…"
            onChange={onTextChange}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            linkToPreview={{
              repoName: repoAddress.name,
              repoLocation: repoAddress.location,
              pipelineName,
              isJob,
            }}
            flattenGraphsEnabled={flattenGraphsEnabled}
            flattenGraphs={flattenGraphs}
            setFlattenGraphs={() => {
              onFlattenGraphsChange(!flattenGraphs);
            }}
          />
        </ShortcutHandler>
      </Popover>
    </Box>
  );
};

const PopoverErrorWrap = styled.div`
  padding: 4px 8px;
  border-radius: 2px;
  border: 1px solid ${Colors.accentRed()};
  background: ${Colors.backgroundRed()};
  color: ${Colors.textRed()};
`;
