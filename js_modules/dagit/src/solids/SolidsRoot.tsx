import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import * as querystring from 'query-string';
import * as React from 'react';
import {useHistory, useLocation} from 'react-router-dom';
import {AutoSizer, CellMeasurer, CellMeasurerCache, List} from 'react-virtualized';
import styled from 'styled-components/macro';

import {Loading} from 'src/Loading';
import {SolidTypeSignature} from 'src/SolidTypeSignature';
import {SplitPanelContainer} from 'src/SplitPanelContainer';
import {
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from 'src/TokenizingField';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {SolidDetailScrollContainer, UsedSolidDetails} from 'src/solids/SolidDetailsRoot';
import {
  SolidsRootQuery,
  SolidsRootQuery_repositoryOrError_Repository_usedSolids,
} from 'src/solids/types/SolidsRootQuery';
import {FontFamily} from 'src/ui/styles';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

function flatUniq(arrs: string[][]) {
  const results: {[key: string]: boolean} = {};
  for (const arr of arrs) {
    for (const item of arr) {
      results[item] = true;
    }
  }
  return Object.keys(results).sort((a, b) => a.localeCompare(b));
}

type Solid = SolidsRootQuery_repositoryOrError_Repository_usedSolids;

function searchSuggestionsForSolids(solids: Solid[]): SuggestionProvider[] {
  return [
    {
      token: 'name',
      values: () => solids.map((s) => s.definition.name),
    },
    {
      token: 'pipeline',
      values: () => flatUniq(solids.map((s) => s.invocations.map((i) => i.pipeline.name))),
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
      if (item.token === 'pipeline' && !s.invocations.some((i) => i.pipeline.name === item.value)) {
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
  name?: string;
  repoAddress: RepoAddress;
}

export const SolidsRoot: React.FC<Props> = (props) => {
  const {name, repoAddress} = props;
  useDocumentTitle('Solids');
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SolidsRootQuery>(SOLIDS_ROOT_QUERY, {
    variables: {repositorySelector},
  });

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
        width: '100%',
        height: '100%',
      }}
    >
      <Loading queryResult={queryResult}>
        {({repositoryOrError}) => {
          if (repositoryOrError?.__typename === 'Repository' && repositoryOrError.usedSolids) {
            return (
              <SolidsRootWithData
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

const SolidsRootWithData: React.FC<Props & {usedSolids: Solid[]}> = (props) => {
  const {name, repoAddress, usedSolids} = props;
  const history = useHistory();
  const location = useLocation();

  const {q, typeExplorer} = querystring.parse(location.search);
  const suggestions = searchSuggestionsForSolids(usedSolids);
  const search = tokenizedValuesFromString((q as string) || '', suggestions);
  const filtered = filterSolidsWithSearch(usedSolids, search);

  const selected = usedSolids.find((s) => s.definition.name === name);

  const onSearch = (search: TokenizingFieldValue[]) => {
    history.push({
      search: `?${querystring.stringify({q: stringFromValue(search)})}`,
    });
  };

  const onClickSolid = (defName: string) => {
    history.push(
      workspacePathFromAddress(repoAddress, `/solids/${defName}?${querystring.stringify({q})}`),
    );
  };

  React.useEffect(() => {
    // If the user has typed in a search that brings us to a single result, autoselect it
    if (filtered.length === 1 && (!selected || filtered[0] !== selected)) {
      onClickSolid(filtered[0].definition.name);
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
          `/pipelines/${pipelineName}/${handleID.split('.').join('/')}`,
        ),
      );
    },
    [history, repoAddress],
  );

  return (
    <SplitPanelContainer
      identifier={'solids'}
      firstInitialPercent={40}
      firstMinSize={420}
      first={
        <SolidListColumnContainer>
          <div
            style={{
              padding: '15px 10px',
              borderBottom: `1px solid ${Colors.LIGHT_GRAY2}`,
            }}
          >
            <TokenizingField
              values={search}
              onChange={(search) => onSearch(search)}
              suggestionProviders={suggestions}
              placeholder={'Filter by name or input/output type...'}
            />
          </div>
          <div style={{flex: 1}}>
            <AutoSizer>
              {({height, width}) => (
                <SolidList
                  height={height}
                  width={width}
                  selected={selected}
                  onClickSolid={onClickSolid}
                  items={filtered.sort((a, b) =>
                    a.definition.name.localeCompare(b.definition.name),
                  )}
                />
              )}
            </AutoSizer>
          </div>
        </SolidListColumnContainer>
      }
      second={
        selected ? (
          <SolidDetailScrollContainer>
            <UsedSolidDetails
              name={selected.definition.name}
              onClickInvocation={onClickInvocation}
              repoAddress={repoAddress}
            />
          </SolidDetailScrollContainer>
        ) : (
          <NonIdealState
            title="No solid selected"
            description="Select a solid to see its definition and invocations."
          />
        )
      }
    />
  );
};

interface SolidListProps {
  items: Solid[];
  width: number;
  height: number;
  selected: Solid | undefined;
  onClickSolid: (name: string) => void;
}

const SolidList: React.FunctionComponent<SolidListProps> = (props) => {
  const cache = React.useRef(new CellMeasurerCache({defaultHeight: 60, fixedWidth: true}));

  // Reset our cell sizes when the panel's width is changed. This is similar to a useEffect
  // but we need it to run /before/ the render not just after it completes.
  const lastWidth = React.useRef(props.width);
  if (props.width !== lastWidth.current) {
    cache.current.clearAll();
    lastWidth.current = props.width;
  }

  return (
    <List
      width={props.width}
      height={props.height}
      rowCount={props.items.length}
      rowHeight={cache.current.rowHeight}
      rowRenderer={({parent, index, key, style}) => {
        const solid = props.items[index];
        return (
          <CellMeasurer cache={cache.current} index={index} parent={parent} key={key}>
            <SolidListItem
              style={style}
              selected={solid === props.selected}
              onClick={() => props.onClickSolid(solid.definition.name)}
            >
              <SolidName>{solid.definition.name}</SolidName>
              <SolidTypeSignature definition={solid.definition} />
            </SolidListItem>
          </CellMeasurer>
        );
      }}
      overscanRowCount={10}
    />
  );
};

export const SOLIDS_ROOT_QUERY = gql`
  query SolidsRootQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolids {
          __typename
          definition {
            name
            ...SolidTypeSignatureFragment
          }
          invocations {
            __typename
            pipeline {
              name
            }
          }
        }
      }
    }
  }
  ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
`;

const SolidListItem = styled.div<{selected: boolean}>`
  background: ${({selected}) => (selected ? Colors.BLUE3 : Colors.WHITE)};
  color: ${({selected}) => (selected ? Colors.WHITE : Colors.DARK_GRAY3)};
  font-size: 14px;
  display: flex;
  flex-direction: column;
  padding: 10px 15px;
  user-select: none;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  & > code.bp3-code {
    color: ${({selected}) => (selected ? Colors.WHITE : Colors.DARK_GRAY3)};
    background: transparent;
    fontfamily: ${FontFamily.monospace};
    padding: 5px 0 0 0;
  }
`;

const SolidName = styled.div`
  flex: 1;
  font-weight: 600;
`;

const SolidListColumnContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;
