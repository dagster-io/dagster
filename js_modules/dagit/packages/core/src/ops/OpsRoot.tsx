import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Colors,
  NonIdealState,
  SplitPanelContainer,
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
  FontFamily,
} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {useHistory, useLocation, useParams} from 'react-router-dom';
import {AutoSizer, CellMeasurer, CellMeasurerCache, List} from 'react-virtualized';
import styled from 'styled-components/macro';

import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {OpDetailScrollContainer, UsedSolidDetails} from './OpDetailsRoot';
import {OpTypeSignature, OP_TYPE_SIGNATURE_FRAGMENT} from './OpTypeSignature';
import {
  OpsRootQuery,
  OpsRootQueryVariables,
  OpsRootQuery_repositoryOrError_Repository_usedSolids,
} from './types/OpsRootQuery';

function flatUniq(arrs: string[][]) {
  const results: {[key: string]: boolean} = {};
  for (const arr of arrs) {
    for (const item of arr) {
      results[item] = true;
    }
  }
  return Object.keys(results).sort((a, b) => a.localeCompare(b));
}

type Solid = OpsRootQuery_repositoryOrError_Repository_usedSolids;

function searchSuggestionsForOps(solids: Solid[]): SuggestionProvider[] {
  return [
    {
      token: 'name',
      values: () => solids.map((s) => s.definition.name),
    },
    {
      token: 'job',
      values: () =>
        flatUniq(
          solids.map((s) =>
            s.invocations.filter((i) => !i.pipeline.isJob).map((i) => i.pipeline.name),
          ),
        ),
    },
    {
      token: 'pipeline',
      values: () =>
        flatUniq(
          solids.map((s) =>
            s.invocations.filter((i) => i.pipeline.isJob).map((i) => i.pipeline.name),
          ),
        ),
    },
    {
      token: 'input',
      values: () =>
        flatUniq(solids.map((s) => s.definition.inputDefinitions.map((d) => d.type.displayName))),
    },
    {
      token: 'output',
      values: () =>
        flatUniq(solids.map((s) => s.definition.outputDefinitions.map((d) => d.type.displayName))),
    },
  ];
}

function filterSolidsWithSearch(solids: Solid[], search: TokenizingFieldValue[]) {
  return solids.filter((s) => {
    for (const item of search) {
      if (
        (item.token === 'name' || item.token === undefined) &&
        !s.definition.name.startsWith(item.value)
      ) {
        return false;
      }
      if (
        (item.token === 'pipeline' || item.token === 'job') &&
        !s.invocations.some((i) => i.pipeline.name === item.value)
      ) {
        return false;
      }
      if (
        item.token === 'input' &&
        !s.definition.inputDefinitions.some((i) => i.type.displayName.startsWith(item.value))
      ) {
        return false;
      }
      if (
        item.token === 'output' &&
        !s.definition.outputDefinitions.some((i) => i.type.displayName.startsWith(item.value))
      ) {
        return false;
      }
    }
    return true;
  });
}

interface Props {
  repoAddress: RepoAddress;
}

export const OpsRoot: React.FC<Props> = (props) => {
  useTrackPageView();
  useDocumentTitle('Ops');

  const {name} = useParams<{name?: string}>();
  const {repoAddress} = props;

  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<OpsRootQuery, OpsRootQueryVariables>(OPS_ROOT_QUERY, {
    variables: {repositorySelector},
  });

  return (
    <div style={{height: '100%'}}>
      <Loading queryResult={queryResult}>
        {({repositoryOrError}) => {
          if (repositoryOrError?.__typename === 'Repository' && repositoryOrError.usedSolids) {
            return (
              <OpsRootWithData
                {...props}
                name={name}
                repoAddress={repoAddress}
                usedSolids={repositoryOrError.usedSolids}
              />
            );
          }
          return null;
        }}
      </Loading>
    </div>
  );
};

const OpsRootWithData: React.FC<Props & {name?: string; usedSolids: Solid[]}> = (props) => {
  const {name, repoAddress, usedSolids} = props;
  const history = useHistory();
  const location = useLocation();

  const {q, typeExplorer} = qs.parse(location.search, {ignoreQueryPrefix: true});
  const suggestions = searchSuggestionsForOps(usedSolids);
  const search = tokenizedValuesFromString((q as string) || '', suggestions);
  const filtered = filterSolidsWithSearch(usedSolids, search);

  const selected = usedSolids.find((s) => s.definition.name === name);

  const onSearch = (search: TokenizingFieldValue[]) => {
    history.replace({
      search: `?${qs.stringify({q: stringFromValue(search)})}`,
    });
  };

  const onClickOp = (defName: string) => {
    history.replace(workspacePathFromAddress(repoAddress, `/ops/${defName}?${qs.stringify({q})}`));
  };

  React.useEffect(() => {
    // If the user has typed in a search that brings us to a single result, autoselect it
    if (filtered.length === 1 && (!selected || filtered[0] !== selected)) {
      onClickOp(filtered[0].definition.name);
    }

    // If the user has clicked a type, translate it into a search
    if (typeof typeExplorer === 'string') {
      onSearch([...search, {token: 'input', value: typeExplorer}]);
    }
  });

  const onClickInvocation = React.useCallback(
    ({pipelineName, handleID}) => {
      history.push(
        workspacePathFromAddress(
          repoAddress,
          `/pipeline_or_job/${pipelineName}/${handleID.split('.').join('/')}`,
        ),
      );
    },
    [history, repoAddress],
  );

  return (
    <div style={{height: '100%', display: 'flex'}}>
      <SplitPanelContainer
        identifier="ops"
        firstInitialPercent={40}
        firstMinSize={420}
        first={
          <OpListColumnContainer>
            <Box
              padding={{vertical: 12, horizontal: 24}}
              border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
            >
              <TokenizingField
                values={search}
                onChange={(search) => onSearch(search)}
                suggestionProviders={suggestions}
                placeholder="Filter by name or input/output type..."
              />
            </Box>
            <div style={{flex: 1}}>
              <AutoSizer nonce={window.__webpack_nonce__}>
                {({height, width}) => (
                  <OpList
                    height={height}
                    width={width}
                    selected={selected}
                    onClickOp={onClickOp}
                    items={filtered.sort((a, b) =>
                      a.definition.name.localeCompare(b.definition.name),
                    )}
                  />
                )}
              </AutoSizer>
            </div>
          </OpListColumnContainer>
        }
        second={
          selected ? (
            <OpDetailScrollContainer>
              <UsedSolidDetails
                name={selected.definition.name}
                onClickInvocation={onClickInvocation}
                repoAddress={repoAddress}
              />
            </OpDetailScrollContainer>
          ) : (
            <Box padding={{vertical: 64}}>
              <NonIdealState
                icon="no-results"
                title="No op selected"
                description="Select an op to see its definition and invocations"
              />
            </Box>
          )
        }
      />
    </div>
  );
};

interface OpListProps {
  items: Solid[];
  width: number;
  height: number;
  selected: Solid | undefined;
  onClickOp: (name: string) => void;
}

const OpList: React.FC<OpListProps> = (props) => {
  const {items, selected} = props;
  const cache = React.useRef(new CellMeasurerCache({defaultHeight: 60, fixedWidth: true}));

  // Reset our cell sizes when the panel's width is changed. This is similar to a useEffect
  // but we need it to run /before/ the render not just after it completes.
  const lastWidth = React.useRef(props.width);
  if (props.width !== lastWidth.current) {
    cache.current.clearAll();
    lastWidth.current = props.width;
  }

  const selectedIndex = selected ? items.findIndex((item) => item === selected) : undefined;

  return (
    <Container>
      <List
        width={props.width}
        height={props.height}
        rowCount={props.items.length}
        rowHeight={cache.current.rowHeight}
        scrollToIndex={selectedIndex}
        className="solids-list"
        rowRenderer={({parent, index, key, style}) => {
          const solid = props.items[index];
          return (
            <CellMeasurer cache={cache.current} index={index} parent={parent} key={key}>
              <OpListItem
                style={style}
                selected={solid === props.selected}
                onClick={() => props.onClickOp(solid.definition.name)}
              >
                <OpName>{solid.definition.name}</OpName>
                <OpTypeSignature definition={solid.definition} />
              </OpListItem>
            </CellMeasurer>
          );
        }}
        overscanRowCount={10}
      />
    </Container>
  );
};

const Container = styled.div`
  .solids-list:focus {
    outline: none;
  }
`;

const OPS_ROOT_QUERY = gql`
  query OpsRootQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolids {
          __typename
          definition {
            name
            ...OpTypeSignatureFragment
          }
          invocations {
            __typename
            pipeline {
              id
              isJob
              name
            }
          }
        }
      }
    }
  }
  ${OP_TYPE_SIGNATURE_FRAGMENT}
`;

const OpListItem = styled.div<{selected: boolean}>`
  background: ${({selected}) => (selected ? Colors.Gray100 : Colors.White)};
  box-shadow: ${({selected}) => (selected ? Colors.HighlightGreen : 'transparent')} 4px 0 0 inset,
    ${Colors.KeylineGray} 0 -1px 0 inset;
  color: ${Colors.Gray800};
  cursor: pointer;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  padding: 12px 24px;
  user-select: none;

  & > code.bp3-code {
    color: ${Colors.Gray800};
    background: transparent;
    font-family: ${FontFamily.monospace};
    padding: 5px 0 0 0;
  }
`;

const OpName = styled.div`
  flex: 1;
  font-weight: 600;
`;

const OpListColumnContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;
