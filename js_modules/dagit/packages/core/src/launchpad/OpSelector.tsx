import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {filterByQuery} from '../app/GraphQueryImpl';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {OP_NODE_INVOCATION_FRAGMENT} from '../graph/OpNode';
import {ColorsWIP} from '../ui/Colors';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Popover} from '../ui/Popover';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {OpSelectorQuery} from './types/OpSelectorQuery';

interface IOpSelectorProps {
  pipelineName: string;
  serverProvidedSubsetError?: {message: string};
  value: string[] | null;
  query: string | null;
  onChange: (value: string[] | null, query: string | null) => void;
  repoAddress: RepoAddress;
}

const SOLID_SELECTOR_QUERY = gql`
  query OpSelectorQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      __typename
      ... on Pipeline {
        id
        name
        solids {
          name
          ...OpNodeInvocationFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
  ${OP_NODE_INVOCATION_FRAGMENT}
`;

export const OpSelector = (props: IOpSelectorProps) => {
  const {serverProvidedSubsetError, onChange, pipelineName, repoAddress} = props;
  const [focused, setFocused] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const selector = {...repoAddressToSelector(repoAddress), pipelineName};
  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  const {data, loading} = useQuery<OpSelectorQuery>(SOLID_SELECTOR_QUERY, {
    variables: {selector},
    fetchPolicy: 'cache-and-network',
  });

  const query = props.query || '*';
  const ops = data?.pipelineOrError.__typename === 'Pipeline' ? data.pipelineOrError.solids : [];
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
    <div>
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
            width={(query !== '*' && query !== '') || focused ? 350 : 90}
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
              pipelineName: pipelineName,
              isJob,
            }}
          />
        </ShortcutHandler>
      </Popover>
    </div>
  );
};

const PopoverErrorWrap = styled.div`
  padding: 4px 8px;
  border-radius: 2px;
  border: 1px solid ${ColorsWIP.Red500};
  background: ${ColorsWIP.Red200};
  color: ${ColorsWIP.Red700};
`;
