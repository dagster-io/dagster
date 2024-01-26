import {Box, Colors, NonIdealState, TextInputContainer} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {useAssetGraphExplorerFilters} from './AssetGraphExplorerFilters';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {GraphData, graphHasCycles} from './Utils';
import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {AssetGraphFetchScope, AssetGraphQueryItem, useAssetGraphData} from './useAssetGraphData';
import {AssetLocation} from './useFindAssetLocation';
import {AssetKey} from '../assets/types';
import {AssetGroupSelector} from '../graphql/types';
import {useStartTrace} from '../performance';
import {GraphExplorerOptions} from '../pipelines/GraphExplorer';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {Loading} from '../ui/Loading';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {AssetGraphExplorerWithData} from './AssetGraphExplorerWithData';

export type AssetNode = AssetNodeForGraphQueryFragment;

type OptionalFilters =
  | {
      filters: {
        groups: AssetGroupSelector[];
        computeKindTags: string[];
      };
      setFilters: (updates: {groups: AssetGroupSelector[]; computeKindTags: string[]}) => void;
    }
  | {filters?: null; setFilters?: null};

type Props = {
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  fetchOptions: AssetGraphFetchScope;

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onNavigateToSourceAssetNode: (node: AssetLocation) => void;
  isGlobalGraph?: boolean;
  trace?: ReturnType<typeof useStartTrace>;
} & OptionalFilters;

export const MINIMAL_SCALE = 0.6;
export const GROUPS_ONLY_SCALE = 0.15;

const emptyArray: any[] = [];

export const AssetGraphExplorer = (props: Props) => {
  const {fetchResult, assetGraphData, fullAssetGraphData, graphQueryItems, allAssetKeys} =
    useAssetGraphData(props.explorerPath.opsQuery, {
      ...props.fetchOptions,
      computeKinds: props.filters?.computeKindTags,
    });

  const {visibleRepos} = React.useContext(WorkspaceContext);

  const assetGroups: AssetGroupSelector[] = React.useMemo(() => {
    return visibleRepos.flatMap((repo) =>
      repo.repository.assetGroups.map((g) => ({
        groupName: g.groupName,
        repositoryLocationName: repo.repositoryLocation.name,
        repositoryName: repo.repository.name,
      })),
    );
  }, [visibleRepos]);

  const {explorerPath, onChangeExplorerPath} = props;

  const {button, filterBar} = useAssetGraphExplorerFilters({
    nodes: React.useMemo(
      () => (fullAssetGraphData ? Object.values(fullAssetGraphData.nodes) : []),
      [fullAssetGraphData],
    ),
    assetGroups,
    visibleAssetGroups: React.useMemo(() => props.filters?.groups || [], [props.filters?.groups]),
    setGroupFilters: React.useCallback(
      (groups: AssetGroupSelector[]) => props.setFilters?.({...props.filters, groups}),
      [props],
    ),
    computeKindTags: props.filters?.computeKindTags || emptyArray,
    setComputeKindTags: React.useCallback(
      (tags: string[]) =>
        props.setFilters?.({
          ...props.filters,
          computeKindTags: tags,
        }),
      [props],
    ),
    explorerPath: explorerPath.opsQuery,
    clearExplorerPath: React.useCallback(() => {
      onChangeExplorerPath(
        {
          ...explorerPath,
          opsQuery: '',
        },
        'push',
      );
    }, [explorerPath, onChangeExplorerPath]),
  });

  return (
    <Loading allowStaleData queryResult={fetchResult}>
      {() => {
        if (!assetGraphData || !allAssetKeys || !fullAssetGraphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const hasCycles = graphHasCycles(assetGraphData);

        if (hasCycles) {
          return (
            <NonIdealState
              icon="error"
              title="Cycle detected"
              description="Assets dependencies form a cycle"
            />
          );
        }
        return (
          <AssetGraphExplorerWithData
            key={props.explorerPath.pipelineName}
            assetGraphData={assetGraphData}
            fullAssetGraphData={fullAssetGraphData}
            allAssetKeys={allAssetKeys}
            graphQueryItems={graphQueryItems}
            filterBar={filterBar}
            filterButton={button}
            {...props}
          />
        );
      }}
    </Loading>
  );
};

export type WithDataProps = Props & {
  allAssetKeys: AssetKey[];
  assetGraphData: GraphData;
  fullAssetGraphData: GraphData;
  graphQueryItems: AssetGraphQueryItem[];

  filterButton?: React.ReactNode;
  filterBar?: React.ReactNode;
  isGlobalGraph?: boolean;
  trace?: ReturnType<typeof useStartTrace>;
};

interface KeyboardTagProps {
  $withinTooltip?: boolean;
}

export const KeyboardTag = styled.div<KeyboardTagProps>`
  ${(props) => {
    return props.$withinTooltip ? `color: ${Colors.accentWhite()}` : `color: ${Colors.textLight()}`;
  }};
  background: ${Colors.backgroundGray()};
  border-radius: 4px;
  padding: 2px 4px;
  margin-left: 6px;
  font-size: 12px;
`;

export const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;

  foreignObject.group {
    transition: opacity 300ms linear;
  }
`;

export const TopbarWrapper = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  background: ${Colors.backgroundDefault()};
  gap: 12px;
  align-items: center;
  border-bottom: 1px solid ${Colors.keylineDefault()};
`;

export const GraphQueryInputFlexWrap = styled.div`
  flex: 1;

  > ${Box} {
    ${TextInputContainer} {
      width: 100%;
    }
    > * {
      display: block;
      width: 100%;
    }
  }
`;
