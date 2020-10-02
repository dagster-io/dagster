import {Colors, Intent, Popover} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import styled from 'styled-components/macro';

import {usePipelineSelector} from 'src/DagsterRepositoryContext';
import {filterByQuery} from 'src/GraphQueryImpl';
import {GraphQueryInput} from 'src/GraphQueryInput';
import {ShortcutHandler} from 'src/ShortcutHandler';
import {
  SolidSelectorQuery,
  SolidSelectorQuery_pipelineOrError,
  SolidSelectorQuery_pipelineOrError_Pipeline_solids,
} from 'src/execute/types/SolidSelectorQuery';
import {PipelineGraph} from 'src/graph/PipelineGraph';
import {SVGViewport} from 'src/graph/SVGViewport';
import {getDagrePipelineLayout} from 'src/graph/getFullSolidLayout';

interface ISolidSelectorProps {
  pipelineName: string;
  serverProvidedSubsetError?: {message: string};
  value: string[] | null;
  query: string | null;
  onChange: (value: string[] | null, query: string | null) => void;
  onRequestClose?: () => void;
}

interface SolidSelectorModalProps {
  pipelineOrError: SolidSelectorQuery_pipelineOrError;
  queryResultSolids: SolidSelectorQuery_pipelineOrError_Pipeline_solids[];
  errorMessage: string | null;
}

class SolidSelectorModal extends React.PureComponent<SolidSelectorModalProps> {
  graphRef = React.createRef<PipelineGraph>();

  render() {
    const {pipelineOrError, queryResultSolids, errorMessage} = this.props;

    if (pipelineOrError.__typename !== 'Pipeline') {
      return (
        <SolidSelectorModalContainer>
          {errorMessage && <ModalErrorOverlay>{errorMessage}</ModalErrorOverlay>}
        </SolidSelectorModalContainer>
      );
    }

    return (
      <SolidSelectorModalContainer>
        {errorMessage && <ModalErrorOverlay>{errorMessage}</ModalErrorOverlay>}
        <PipelineGraph
          ref={this.graphRef}
          backgroundColor={Colors.WHITE}
          pipelineName={pipelineOrError.name}
          solids={queryResultSolids}
          layout={getDagrePipelineLayout(queryResultSolids)}
          interactor={SVGViewport.Interactors.None}
          focusSolids={[]}
          highlightedSolids={[]}
        />
      </SolidSelectorModalContainer>
    );
  }
}

const SOLID_SELECTOR_QUERY = gql`
  query SolidSelectorQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      __typename
      ... on Pipeline {
        id
        name
        solids {
          name
          ...PipelineGraphSolidFragment
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
  ${PipelineGraph.fragments.PipelineGraphSolidFragment}
`;

export const SolidSelector = (props: ISolidSelectorProps) => {
  const {serverProvidedSubsetError, query, onChange} = props;
  const [pending, setPending] = React.useState<string>(query || '*');
  const [focused, setFocused] = React.useState(false);
  const selector = usePipelineSelector(props.pipelineName);
  const {data, loading} = useQuery<SolidSelectorQuery>(SOLID_SELECTOR_QUERY, {
    variables: {selector},
    fetchPolicy: 'cache-and-network',
  });

  React.useEffect(() => {
    setPending(query || '*');
  }, [query, focused]);

  const queryResultSolids =
    data?.pipelineOrError.__typename === 'Pipeline'
      ? filterByQuery(data!.pipelineOrError.solids, pending).all
      : [];

  const pipelineErrorMessage =
    data?.pipelineOrError.__typename !== 'Pipeline' ? data?.pipelineOrError.message || null : null;

  if (pipelineErrorMessage) {
    console.error(`Could not load pipeline ${props.pipelineName}`);
  }

  const errorMessage =
    !loading && (queryResultSolids.length === 0 || pending.length === 0)
      ? `You must provide a valid solid query or * to execute the entire pipeline.`
      : serverProvidedSubsetError
      ? serverProvidedSubsetError.message
      : pipelineErrorMessage;

  const onCommitPendingValue = (applied: string) => {
    if (data?.pipelineOrError.__typename !== 'Pipeline') {
      return;
    }

    if (applied === '') {
      applied = '*';
    }
    const queryResultSolids = filterByQuery(data.pipelineOrError.solids, applied).all;

    // If all solids are returned, we set the subset to null rather than sending
    // a comma separated list of evey solid to the API
    if (queryResultSolids.length === data.pipelineOrError.solids.length) {
      onChange(null, applied);
    } else {
      onChange(
        queryResultSolids.map((s) => s.name),
        applied,
      );
    }
  };

  return (
    <div style={{position: 'relative'}}>
      <Popover
        autoFocus={false}
        isOpen={focused}
        minimal
        modifiers={{arrow: {enabled: false}, offset: {enabled: true, offset: '0, 8px'}}}
        position="bottom-left"
      >
        <ShortcutHandler shortcutLabel={'⌥S'} shortcutFilter={(e) => e.keyCode === 83 && e.altKey}>
          <GraphQueryInput
            width={(pending !== '*' && pending !== '') || focused ? 350 : 90}
            intent={errorMessage ? Intent.DANGER : Intent.NONE}
            items={
              data?.pipelineOrError.__typename === 'Pipeline' ? data?.pipelineOrError.solids : []
            }
            value={pending}
            placeholder="Type a Solid Subset"
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
          />
        </ShortcutHandler>
        {data?.pipelineOrError && (
          <SolidSelectorModal
            pipelineOrError={data?.pipelineOrError}
            errorMessage={errorMessage}
            queryResultSolids={queryResultSolids}
          />
        )}
      </Popover>
    </div>
  );
};

const SolidSelectorModalContainer = styled.div`
  border-radius: 4px;
  width: 60vw;
  height: 60vh;
  background: ${Colors.WHITE};
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
  border: 1px solid ${Colors.RED3};
  background: ${Colors.RED5};
  color: white;
`;
