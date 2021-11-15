import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {filterByQuery} from '../app/GraphQueryImpl';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {PipelineGraph, PIPELINE_GRAPH_OP_FRAGMENT} from '../graph/PipelineGraph';
import {SVGViewport} from '../graph/SVGViewport';
import {getDagrePipelineLayout} from '../graph/getFullOpLayout';
import {ColorsWIP} from '../ui/Colors';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Popover} from '../ui/Popover';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  OpSelectorQuery,
  OpSelectorQuery_pipelineOrError,
  OpSelectorQuery_pipelineOrError_Pipeline_solids,
} from './types/OpSelectorQuery';

interface IOpSelectorProps {
  pipelineName: string;
  serverProvidedSubsetError?: {message: string};
  value: string[] | null;
  query: string | null;
  onChange: (value: string[] | null, query: string | null) => void;
  onRequestClose?: () => void;
  repoAddress: RepoAddress;
}

interface OpSelectorModalProps {
  pipelineOrError: OpSelectorQuery_pipelineOrError;
  queryResultOps: OpSelectorQuery_pipelineOrError_Pipeline_solids[];
  errorMessage: string | null;
}

class OpSelectorModal extends React.PureComponent<OpSelectorModalProps> {
  graphRef = React.createRef<PipelineGraph>();

  render() {
    const {pipelineOrError, queryResultOps, errorMessage} = this.props;

    if (pipelineOrError.__typename !== 'Pipeline') {
      return (
        <OpSelectorModalContainer>
          {errorMessage && <ModalErrorOverlay>{errorMessage}</ModalErrorOverlay>}
        </OpSelectorModalContainer>
      );
    }

    return (
      <OpSelectorModalContainer>
        {errorMessage && <ModalErrorOverlay>{errorMessage}</ModalErrorOverlay>}
        <PipelineGraph
          ref={this.graphRef}
          backgroundColor={ColorsWIP.White}
          pipelineName={pipelineOrError.name}
          ops={queryResultOps}
          layout={getDagrePipelineLayout(queryResultOps)}
          interactor={SVGViewport.Interactors.None}
          focusOps={[]}
          highlightedOps={[]}
        />
      </OpSelectorModalContainer>
    );
  }
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
          ...PipelineGraphOpFragment
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
  ${PIPELINE_GRAPH_OP_FRAGMENT}
`;

export const OpSelector = (props: IOpSelectorProps) => {
  const {serverProvidedSubsetError, query, onChange, pipelineName, repoAddress} = props;
  const [pending, setPending] = React.useState<string>(query || '*');
  const [focused, setFocused] = React.useState(false);
  const selector = {
    ...repoAddressToSelector(repoAddress),
    pipelineName,
  };

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  const inputRef = React.useRef<HTMLInputElement>(null);

  const {data, loading} = useQuery<OpSelectorQuery>(SOLID_SELECTOR_QUERY, {
    variables: {selector},
    fetchPolicy: 'cache-and-network',
  });

  React.useEffect(() => {
    setPending(query || '*');
  }, [query, focused]);

  const queryResultOps =
    data?.pipelineOrError.__typename === 'Pipeline'
      ? filterByQuery(data!.pipelineOrError.solids, pending).all
      : [];

  const pipelineErrorMessage =
    data?.pipelineOrError.__typename !== 'Pipeline' ? data?.pipelineOrError.message || null : null;

  if (pipelineErrorMessage) {
    console.error(`Could not load pipeline ${props.pipelineName}`);
  }

  const invalidResult = !loading && (queryResultOps.length === 0 || pending.length === 0);

  const errorMessage = React.useMemo(() => {
    if (invalidResult) {
      return isJob
        ? `You must provide a valid op query or * to execute the entire job.`
        : `You must provide a valid solid query or * to execute the entire pipeline.`;
    }

    return serverProvidedSubsetError ? serverProvidedSubsetError.message : pipelineErrorMessage;
  }, [invalidResult, isJob, pipelineErrorMessage, serverProvidedSubsetError]);

  const onCommitPendingValue = (applied: string) => {
    if (data?.pipelineOrError.__typename !== 'Pipeline') {
      return;
    }

    if (applied === '') {
      applied = '*';
    }
    const queryResultOps = filterByQuery(data.pipelineOrError.solids, applied).all;

    // If all solids are returned, we set the subset to null rather than sending
    // a comma separated list of evey solid to the API
    if (queryResultOps.length === data.pipelineOrError.solids.length) {
      onChange(null, applied);
    } else {
      onChange(
        queryResultOps.map((s) => s.name),
        applied,
      );
    }
  };

  if (!data?.pipelineOrError) {
    return null;
  }

  return (
    <div>
      <Popover
        isOpen={focused}
        position="bottom-left"
        content={
          <OpSelectorModal
            pipelineOrError={data.pipelineOrError}
            errorMessage={errorMessage}
            queryResultOps={queryResultOps}
          />
        }
      >
        <ShortcutHandler
          shortcutLabel="⌥S"
          shortcutFilter={(e) => e.code === 'KeyS' && e.altKey}
          onShortcut={() => inputRef.current?.focus()}
        >
          <GraphQueryInput
            width={(pending !== '*' && pending !== '') || focused ? 350 : 90}
            intent={errorMessage ? 'danger' : 'none'}
            items={
              data?.pipelineOrError.__typename === 'Pipeline' ? data?.pipelineOrError.solids : []
            }
            value={pending}
            placeholder="Type an op subset…"
            onChange={setPending}
            onBlur={(pending) => {
              onCommitPendingValue(pending);
              setFocused(false);
            }}
            onFocus={() => setFocused(true)}
            onKeyDown={(e) => {
              if (e.isDefaultPrevented()) {
                return;
              }
              if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Escape') {
                e.currentTarget.blur();
              }
            }}
            ref={inputRef}
          />
        </ShortcutHandler>
      </Popover>
    </div>
  );
};

const OpSelectorModalContainer = styled.div`
  border-radius: 4px;
  width: 60vw;
  height: 60vh;
  background: ${ColorsWIP.White};
  & > div {
    border-radius: 4px;
  }
`;

const ModalErrorOverlay = styled.div`
  position: absolute;
  margin: 5px;
  padding: 4px 8px;
  z-index: 2;
  border-radius: 2px;
  border: 1px solid ${ColorsWIP.Red500};
  background: ${ColorsWIP.Red200};
  color: white;
`;
