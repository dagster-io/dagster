import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {
  globalAssetGraphPathFromString,
  globalAssetGraphPathToString,
} from '../../assets/globalAssetGraphPathToString';
import {
  buildAssetKey,
  buildAssetNode,
  buildRepository,
  buildRepositoryLocation,
} from '../../graphql/builders';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {AssetGraphExplorer} from '../AssetGraphExplorer';
import {AssetGraphViewType, buildGraphData, tokenForAssetKey} from '../Utils';

jest.mock('@shared/app/observeEnabled', () => ({
  observeEnabled: jest.fn(() => false),
}));

jest.mock('@shared/asset-selection/input/AssetSelectionInput', () => ({
  AssetSelectionInput: () => <input aria-label="Search and filter assets" />,
}));

jest.mock('@shared/assets/CreateCatalogViewButton', () => ({
  CreateCatalogViewButton: () => null,
}));

jest.mock('@shared/assets/catalog/useCatalogExtraDropdownOptions', () => ({
  useCatalogExtraDropdownOptions: jest.fn(() => []),
}));

jest.mock('../AssetEdges', () => ({
  AssetEdges: () => null,
}));

jest.mock('../AssetGraphBackgroundContextMenu', () => ({
  AssetGraphBackgroundContextMenu: ({children}: {children: React.ReactNode}) => <>{children}</>,
}));

jest.mock('../AssetGraphJobSidebar', () => ({
  AssetGraphJobSidebar: () => <div>job sidebar</div>,
}));

jest.mock('../AssetNode', () => ({
  AssetNode: ({definition}: {definition: {assetKey: {path: string[]}}}) => (
    <button type="button">{definition.assetKey.path[definition.assetKey.path.length - 1]}</button>
  ),
  AssetNodeMinimal: ({definition}: {definition: {assetKey: {path: string[]}}}) => (
    <button type="button">{definition.assetKey.path[definition.assetKey.path.length - 1]}</button>
  ),
  AssetNodeContextMenuWrapper: ({children}: {children: React.ReactNode}) => <>{children}</>,
}));

jest.mock('../AssetNodeFacetSettingsButton', () => ({
  AssetNodeFacetSettingsButton: () => null,
}));

jest.mock('../CollapsedGroupNode', () => ({
  CollapsedGroupNode: () => null,
}));

jest.mock('../ExpandedGroupNode', () => ({
  ExpandedGroupNode: () => null,
  GroupOutline: () => null,
}));

jest.mock('../ForeignNode', () => ({
  AssetNodeLink: () => null,
}));

jest.mock('../GraphSettings', () => ({
  AssetGraphSettingsButton: () => null,
  useLayoutDirectionState: () => ['horizontal', jest.fn()],
}));

jest.mock('../SidebarAssetInfo', () => ({
  SidebarAssetInfo: ({
    graphNode,
    onToggleCollapse,
  }: {
    graphNode: {assetKey: {path: string[]}};
    onToggleCollapse?: () => void;
  }) => (
    <div data-testid="asset-sidebar-info">
      <button type="button" aria-label="Hide details panel" onClick={onToggleCollapse}>
        hide
      </button>
      {graphNode.assetKey.path[graphNode.assetKey.path.length - 1]}
    </div>
  ),
}));

jest.mock('../sidebar/Sidebar', () => ({
  AssetGraphExplorerSidebar: () => <div>left sidebar</div>,
}));

jest.mock('../useAssetGraphData', () => ({
  useFullAssetGraphData: jest.fn(),
  useAssetGraphData: jest.fn(),
}));

jest.mock('../useFindAssetLocation', () => ({
  useFindAssetLocation: () => jest.fn(),
}));

jest.mock('../useNodeDrag', () => ({
  useNodeDrag: () => ({
    onNodeMouseDown: jest.fn(),
    onGroupMouseDown: jest.fn(),
    draggingNodeId: null,
    draggedNodePositions: {},
  }),
}));

jest.mock('../usePositionOverrides', () => ({
  usePositionOverrides: () => ({
    overrides: {},
    updateNodePosition: jest.fn(),
    updateMultiplePositions: jest.fn(),
    resetNodePosition: jest.fn(),
    resetMultiplePositions: jest.fn(),
    resetAllOverrides: jest.fn(),
    hasOverrides: false,
  }),
}));

jest.mock('../../app/AppTopNav/AppTopNavContext', () => ({
  useFullScreenAllowedView: jest.fn(),
  useFullScreen: () => ({
    isFullScreen: false,
    toggleFullScreen: jest.fn(),
  }),
}));

jest.mock('../../app/useFeatureFlags', () => ({
  useFeatureFlags: () => ({
    flagAssetGraphGroupsPerCodeLocation: false,
  }),
}));

jest.mock('../../asset-data/AssetLiveDataProvider', () => ({
  AssetLiveDataRefreshButton: () => null,
}));

jest.mock('../../assets/LaunchAssetExecutionButton', () => ({
  LaunchAssetExecutionButton: () => <button type="button">Materialize selected</button>,
}));

jest.mock('../../graph/SVGViewport', () => {
  const mockReact = jest.requireActual<typeof React>('react');

  return {
    SVGViewport: mockReact.forwardRef(
      (
        {
          children,
          onClick,
        }: {
          children: (args: {scale: number}, viewportRect: any) => React.ReactNode;
          onClick: () => void;
        },
        ref: React.ForwardedRef<unknown>,
      ) => {
        mockReact.useImperativeHandle(ref, () => ({
          zoomToSVGCoords: jest.fn(),
          scaleForSVGBounds: jest.fn(() => 1),
          getScale: jest.fn(() => 1),
          zoomToSVGBox: jest.fn(),
          autocenter: jest.fn(),
          focus: jest.fn(),
        }));

        return (
          <div>
            <button type="button" onClick={onClick}>
              graph background
            </button>
            {children(
              {scale: 1},
              {left: 0, top: 0, right: 1200, bottom: 800, width: 1200, height: 800},
            )}
          </div>
        );
      },
    ),
  };
});

jest.mock('../../graph/asyncGraphLayout', () => ({
  useAssetLayout: jest.fn(),
}));

jest.mock('../../hooks/usePrevious', () => ({
  usePreviousDistinctValue: <T,>(value: T) => value,
}));

jest.mock('../../hooks/useQueryAndLocalStoragePersistedState', () => ({
  useQueryAndLocalStoragePersistedState: jest.fn(() => {
    const mockReact = jest.requireActual<typeof React>('react');
    return mockReact.useState([]);
  }),
}));

jest.mock('../../pipelines/GraphExplorer', () => ({
  OptionsOverlay: ({children}: {children: React.ReactNode}) => <>{children}</>,
  RightInfoPanel: ({children}: {children: React.ReactNode}) => <div>{children}</div>,
  RightInfoPanelContent: ({children}: {children: React.ReactNode}) => <div>{children}</div>,
}));

jest.mock('../../pipelines/GraphNotices', () => ({
  CycleDetectedNotice: () => null,
  EmptyDAGNotice: () => null,
  EntirelyFilteredDAGNotice: () => null,
  InvalidSelectionQueryNotice: () => null,
  LargeDAGNotice: () => null,
  LoadingContainer: ({children}: {children: React.ReactNode}) => <div>{children}</div>,
  LoadingNotice: () => null,
}));

jest.mock('../../ui/IndeterminateLoadingBar', () => ({
  IndeterminateLoadingBar: () => null,
}));

jest.mock('../../util/isIframe', () => ({
  isIframe: () => false,
}));

const {useAssetGraphData, useFullAssetGraphData} = jest.requireMock('../useAssetGraphData') as {
  useAssetGraphData: jest.Mock;
  useFullAssetGraphData: jest.Mock;
};

const {useAssetLayout} = jest.requireMock('../../graph/asyncGraphLayout') as {
  useAssetLayout: jest.Mock;
};

const repo = buildRepository({
  name: 'repo',
  location: buildRepositoryLocation({name: 'location'}),
});

const assetOne = buildAssetNode({
  id: JSON.stringify(['asset_one']),
  assetKey: buildAssetKey({path: ['asset_one']}),
  groupName: 'default',
  repository: repo,
  dependencyKeys: [],
  dependedByKeys: [buildAssetKey({path: ['asset_two']})],
  opNames: ['asset_one'],
});

const assetTwo = buildAssetNode({
  id: JSON.stringify(['asset_two']),
  assetKey: buildAssetKey({path: ['asset_two']}),
  groupName: 'default',
  repository: repo,
  dependencyKeys: [buildAssetKey({path: ['asset_one']})],
  dependedByKeys: [],
  opNames: ['asset_two'],
});

const graphData = buildGraphData([assetOne, assetTwo]);
const layout = {
  width: 1200,
  height: 800,
  edges: [],
  nodes: {
    [JSON.stringify(['asset_one'])]: {
      id: JSON.stringify(['asset_one']),
      bounds: {x: 100, y: 100, width: 250, height: 100},
    },
    [JSON.stringify(['asset_two'])]: {
      id: JSON.stringify(['asset_two']),
      bounds: {x: 450, y: 100, width: 250, height: 100},
    },
  },
  groups: {},
  linkNodeIds: [],
};

const baseExplorerPath = globalAssetGraphPathFromString(
  globalAssetGraphPathToString({
    opsQuery: '',
    opNames: [tokenForAssetKey(assetOne.assetKey)],
  }),
);

const renderExplorer = () => {
  const onNavigateToSourceAssetNode = jest.fn();

  const Wrapper = () => {
    const [explorerPath, setExplorerPath] = React.useState<ExplorerPath>(baseExplorerPath);

    return (
      <AssetGraphExplorer
        options={{preferAssetRendering: true, explodeComposites: true}}
        fetchOptions={{}}
        explorerPath={explorerPath}
        onChangeExplorerPath={(nextPath) => {
          const normalized = globalAssetGraphPathFromString(
            globalAssetGraphPathToString({
              opsQuery: nextPath.opsQuery,
              opNames: nextPath.opNames,
            }),
          );
          setExplorerPath(normalized);
        }}
        onNavigateToSourceAssetNode={onNavigateToSourceAssetNode}
        viewType={AssetGraphViewType.GLOBAL}
      />
    );
  };

  return render(<Wrapper />);
};

beforeEach(() => {
  useFullAssetGraphData.mockReturnValue({fullAssetGraphData: graphData});
  useAssetGraphData.mockReturnValue({
    loading: false,
    assetGraphData: graphData,
    graphQueryItems: [],
    allAssetKeys: [assetOne.assetKey, assetTwo.assetKey],
  });
  useAssetLayout.mockReturnValue({
    layout,
    loading: false,
    error: null,
    async: false,
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('AssetGraphExplorer', () => {
  it('lets users hide the details panel without clearing selection and reopen it later', async () => {
    const user = userEvent.setup();
    renderExplorer();

    const sidebar = screen.getByTestId('asset-sidebar-info');
    expect(sidebar).toHaveTextContent('asset_one');
    expect(screen.queryByRole('button', {name: 'Show details panel'})).not.toBeInTheDocument();
    await user.click(within(sidebar).getByRole('button', {name: 'Hide details panel'}));
    expect(screen.queryByTestId('asset-sidebar-info')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', {name: 'asset_two'}));
    expect(screen.queryByTestId('asset-sidebar-info')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', {name: 'Show details panel'}));
    expect(screen.getByTestId('asset-sidebar-info')).toHaveTextContent('asset_two');
  });

  it('clears selection and removes the details panel when the graph background is clicked', async () => {
    const user = userEvent.setup();
    renderExplorer();

    expect(screen.getByTestId('asset-sidebar-info')).toHaveTextContent('asset_one');
    await user.click(screen.getByRole('button', {name: 'graph background'}));
    expect(screen.queryByTestId('asset-sidebar-info')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', {name: 'Hide details panel'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button', {name: 'Show details panel'})).not.toBeInTheDocument();
  });
});
