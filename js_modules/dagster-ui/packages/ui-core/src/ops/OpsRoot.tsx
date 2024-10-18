import {
  Box,
  Colors,
  MiddleTruncate,
  NonIdealState,
  SplitPanelContainer,
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import qs from 'qs';
import * as React from 'react';
import {useMemo, useRef} from 'react';
import {useHistory, useLocation, useParams} from 'react-router-dom';
import styled from 'styled-components';

import {OpDetailScrollContainer, UsedSolidDetails} from './OpDetailsRoot';
import {OP_TYPE_SIGNATURE_FRAGMENT} from './OpTypeSignature';
import {gql, useQuery} from '../apollo-client';
import {OpsRootQuery, OpsRootQueryVariables, OpsRootUsedSolidFragment} from './types/OpsRoot.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {COMMON_COLLATOR} from '../app/Util';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Loading} from '../ui/Loading';
import {Container, Inner, Row} from '../ui/VirtualizedTable';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

function flatUniq(arrs: string[][]) {
  const results: {[key: string]: boolean} = {};
  for (const arr of arrs) {
    for (const item of arr) {
      results[item] = true;
    }
  }
  return Object.keys(results).sort((a, b) => a.localeCompare(b));
}

type Solid = OpsRootUsedSolidFragment;

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

export const OpsRoot = (props: Props) => {
  useTrackPageView();
  useDocumentTitle('Ops');

  const {name} = useParams<{name?: string}>();
  const {repoAddress} = props;

  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<OpsRootQuery, OpsRootQueryVariables>(OPS_ROOT_QUERY, {
    variables: {repositorySelector},
  });

  return (
    <div style={{flex: 1, minHeight: 0}}>
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

interface OpsRootWithDataProps extends Props {
  name?: string;
  usedSolids: Solid[];
}

export const OpsRootWithData = (props: OpsRootWithDataProps) => {
  const {name, repoAddress, usedSolids} = props;
  const history = useHistory();
  const location = useLocation();

  const {q, typeExplorer} = qs.parse(location.search, {ignoreQueryPrefix: true});
  const suggestions = searchSuggestionsForOps(usedSolids);
  const search = tokenizedValuesFromString((q as string) || '', suggestions);
  const filtered = filterSolidsWithSearch(usedSolids, search);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) =>
      COMMON_COLLATOR.compare(a.definition.name, b.definition.name),
    );
  }, [filtered]);

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
    if (sorted.length === 1 && (!selected || sorted[0] !== selected)) {
      onClickOp(sorted[0]!.definition.name);
    }

    // If the user has clicked a type, translate it into a search
    if (typeof typeExplorer === 'string') {
      onSearch([...search, {token: 'input', value: typeExplorer}]);
    }
  });

  const onClickInvocation: React.ComponentProps<typeof UsedSolidDetails>['onClickInvocation'] =
    React.useCallback(
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
        firstMinSize={448}
        first={
          <OpListColumnContainer>
            <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
              <TokenizingField
                values={search}
                onChange={(search) => onSearch(search)}
                suggestionProviders={suggestions}
                placeholder="Filter by name or input/output type..."
              />
            </Box>
            <div style={{flex: 1, overflow: 'hidden'}}>
              <OpList selected={selected} onClickOp={onClickOp} items={sorted} />
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
  selected: Solid | undefined;
  onClickOp: (name: string) => void;
}

const OpList = (props: OpListProps) => {
  const {items, selected} = props;

  const containerRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 42,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const virtualItems = rowVirtualizer.getVirtualItems();

  const selectedIndex = selected ? items.findIndex((item) => item === selected) : undefined;

  return (
    <Container ref={containerRef}>
      <Inner $totalHeight={totalHeight}>
        {virtualItems.map(({index, size, start}) => {
          const solid = items[index]!;
          return (
            <Row key={solid.definition.name} $height={size} $start={start}>
              <OpListItem
                $selected={selectedIndex === index}
                onClick={() => props.onClickOp(solid.definition.name)}
              >
                <MiddleTruncate text={solid.definition.name} />
              </OpListItem>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};

export const OPS_ROOT_QUERY = gql`
  query OpsRootQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolids {
          ...OpsRootUsedSolid
        }
      }
      ...PythonErrorFragment
    }
  }

  fragment OpsRootUsedSolid on UsedSolid {
    definition {
      name
      ...OpTypeSignatureFragment
    }
    invocations {
      pipeline {
        id
        isJob
        name
      }
    }
  }

  ${OP_TYPE_SIGNATURE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const OpListItem = styled.div<{$selected: boolean}>`
  background: ${({$selected}) =>
    $selected ? Colors.backgroundLight() : Colors.backgroundDefault()};
  box-shadow:
    ${({$selected}) => ($selected ? Colors.accentBlue() : 'transparent')} 4px 0 0 inset,
    ${Colors.keylineDefault()} 0 -1px 0 inset;
  color: ${({$selected}) => ($selected ? Colors.textDefault() : Colors.textLight())};
  cursor: pointer;
  font-size: 14px;
  gap: 8px;
  padding: 12px 24px;
  user-select: none;
  overflow: hidden;
  white-space: nowrap;
`;

const OpListColumnContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;
