import {
  Body,
  Box,
  Button,
  Icon,
  Menu,
  MenuItem,
  Popover,
  ProductTour,
  ProductTourPosition,
  Tooltip,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {KeyboardTag} from './KeyboardTag';
import ShowAndHideNeighborAssetsMP4 from './ShowAndHideNeighborAssets.mp4';
import {AssetLayoutDirection} from './layout';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {useShowStubAssets} from '../app/UserSettingsDialog/useShowStubAssets';
import {assertUnreachable} from '../app/Util';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

type Props = {
  expandedGroups?: string[];
  setExpandedGroups?: (v: string[]) => void;
  allGroups?: string[];
  direction: AssetLayoutDirection;
  setDirection: (d: AssetLayoutDirection) => void;
  hideEdgesToNodesOutsideQuery?: boolean;
  setHideEdgesToNodesOutsideQuery?: (hideEdgesToNodesOutsideQuery: boolean) => void;
  showStubAssets?: boolean | undefined;
  setShowStubAssets?: (showStubAssets: boolean) => void;
};

enum Shortcut {
  Direction = 'Direction',
  ExpandAllGroups = 'ExpandAllGroups',
  HideEdgesToNodesOutsideQuery = 'HideEdgesToNodesOutsideQuery',
  ShowStubAssets = 'ShowStubAssets',
}

type ShortcutInfo =
  | {
      type: Shortcut.Direction;
      label: React.ReactNode;
    }
  | {
      type: Shortcut.ExpandAllGroups;
      expandedGroups: string[];
      allGroups: string[];
      setExpandedGroups: (v: string[]) => void;
      label: React.ReactNode;
    }
  | {
      type: Shortcut.HideEdgesToNodesOutsideQuery;
      hideEdgesToNodesOutsideQuery: boolean;
      setHideEdgesToNodesOutsideQuery: (hideEdgesToNodesOutsideQuery: boolean) => void;
      label: React.ReactNode;
    }
  | {
      type: Shortcut.ShowStubAssets;
      showStubAssets: boolean;
      setShowStubAssets: (showStubAssets: boolean) => void;
      label: React.ReactNode;
    };

export const AssetGraphSettingsButton = ({
  expandedGroups,
  setExpandedGroups,
  allGroups,
  direction,
  setDirection,
  hideEdgesToNodesOutsideQuery,
  setHideEdgesToNodesOutsideQuery,
}: Props) => {
  const hasMultipleGroups = (allGroups?.length ?? 0) > 1;
  const {showStubAssets, setShowStubAssets} = useShowStubAssets();

  const shortcuts = useMemo(() => {
    const shortcuts: ShortcutInfo[] = [
      {
        type: Shortcut.Direction,
        label: (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <div>⌥O</div>-
            <div>
              Change graph orientation to {direction === 'vertical' ? 'horizontal' : 'vertical'}
            </div>
          </Box>
        ),
      },
    ];
    if (hasMultipleGroups && setExpandedGroups) {
      shortcuts.push({
        type: Shortcut.ExpandAllGroups,
        expandedGroups: expandedGroups ?? [],
        allGroups: allGroups ?? [],
        setExpandedGroups,
        label: (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <div>⌥E</div>-
            <div>{expandedGroups?.length === 0 ? 'Expand' : 'Collapse'} all groups</div>
          </Box>
        ),
      });
    }
    if (setHideEdgesToNodesOutsideQuery) {
      shortcuts.push({
        type: Shortcut.HideEdgesToNodesOutsideQuery,
        hideEdgesToNodesOutsideQuery: !!hideEdgesToNodesOutsideQuery,
        setHideEdgesToNodesOutsideQuery,
        label: (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <div>⌥V</div>-
            <div>
              {hideEdgesToNodesOutsideQuery ? 'Show' : 'Hide'} neighbor assets outside of selection
            </div>
          </Box>
        ),
      });
    }
    shortcuts.push({
      type: Shortcut.ShowStubAssets,
      showStubAssets: !!showStubAssets,
      setShowStubAssets,
      label: (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <div>⌥S</div>-<div>{showStubAssets ? 'Hide' : 'Show'} stub assets in catalog</div>
          <Tooltip content="Stub assets are placeholder assets that Dagster automatically creates to represent dependencies that aren't defined in your current code location. ">
            <Icon name="info" />
          </Tooltip>
        </Box>
      ),
    });
    return shortcuts;
  }, [
    direction,
    hasMultipleGroups,
    setExpandedGroups,
    setHideEdgesToNodesOutsideQuery,
    expandedGroups,
    allGroups,
    hideEdgesToNodesOutsideQuery,
    setShowStubAssets,
    showStubAssets,
  ]);

  const shortcutsJsx = useMemo(() => {
    return shortcuts.map((shortcut) => {
      switch (shortcut.type) {
        case Shortcut.Direction:
          return (
            <ShortcutHandler
              key={shortcut.type}
              onShortcut={() => setDirection(direction === 'vertical' ? 'horizontal' : 'vertical')}
              shortcutFilter={(e) => e.altKey && e.code === 'KeyO'}
            >
              <div />
            </ShortcutHandler>
          );
        case Shortcut.ExpandAllGroups:
          return (
            <ShortcutHandler
              key={shortcut.type}
              onShortcut={() =>
                shortcut.setExpandedGroups(
                  shortcut.expandedGroups?.length === 0 ? (shortcut.allGroups ?? []) : [],
                )
              }
              shortcutFilter={(e) => e.altKey && e.code === 'KeyE'}
            >
              <div />
            </ShortcutHandler>
          );
        case Shortcut.HideEdgesToNodesOutsideQuery:
          return (
            <ShortcutHandler
              key={shortcut.type}
              onShortcut={() =>
                shortcut.setHideEdgesToNodesOutsideQuery(!hideEdgesToNodesOutsideQuery)
              }
              shortcutFilter={(e) => e.altKey && e.code === 'KeyV'}
            >
              <div />
            </ShortcutHandler>
          );
        case Shortcut.ShowStubAssets:
          return (
            <ShortcutHandler
              key={shortcut.type}
              onShortcut={() => setShowStubAssets(!showStubAssets)}
              shortcutFilter={(e) => e.altKey && e.code === 'KeyS'}
            >
              <div />
            </ShortcutHandler>
          );
        default:
          assertUnreachable(shortcut);
      }
    });
  }, [
    shortcuts,
    setDirection,
    direction,
    hideEdgesToNodesOutsideQuery,
    setShowStubAssets,
    showStubAssets,
  ]);

  const shortcutLabelJsx = useMemo(
    () => (
      <Box flex={{direction: 'column', gap: 12}}>
        {shortcuts.map((shortcut) => (
          <div key={shortcut.type} style={{whiteSpace: 'nowrap'}}>
            {shortcut.label}
          </div>
        ))}
      </Box>
    ),
    [shortcuts],
  );

  return (
    <>
      <ProductTourWrapper>
        <Popover
          content={
            <AssetGraphSettingsMenu
              expandedGroups={expandedGroups}
              setExpandedGroups={setExpandedGroups}
              allGroups={allGroups}
              hideEdgesToNodesOutsideQuery={hideEdgesToNodesOutsideQuery}
              setHideEdgesToNodesOutsideQuery={setHideEdgesToNodesOutsideQuery}
              direction={direction}
              setDirection={setDirection}
              showStubAssets={showStubAssets}
              setShowStubAssets={setShowStubAssets}
            />
          }
          placement="top"
        >
          <Button icon={<Icon name="settings" />} />
        </Popover>
      </ProductTourWrapper>
      <div style={{position: 'relative', marginTop: -8}}>
        <ShortcutHandler
          shortcutLabel={<Box flex={{direction: 'column', gap: 4}}>{shortcutLabelJsx}</Box>}
        >
          {/* This div is used to position the shortcut label and make sure there's enough space for it to be fully visible */}
          {/* Note we combine all of the shortcuts into a single ShortCutHandler component to ensure that the shortcut labels do not overlap */}
          <div
            style={{
              visibility: 'hidden',
              position: 'absolute',
              bottom: 0,
              left: -32, // To account for the width of the toolbar. We want the shortcut labels to be to the left of the toolbar.
              transform: 'translate(-100%, -100%)', // To make sure the shortcut labels are fully visible.
            }}
          >
            {shortcutLabelJsx}
          </div>
        </ShortcutHandler>
        {shortcutsJsx}
      </div>
    </>
  );
};

export const AssetGraphSettingsMenu = ({
  expandedGroups,
  setExpandedGroups,
  allGroups,
  hideEdgesToNodesOutsideQuery,
  setHideEdgesToNodesOutsideQuery,
  direction,
  setDirection,
}: Omit<Props, 'children'>) => {
  const hasMultipleGroups = (allGroups?.length ?? 0) > 1;
  return (
    <Menu>
      <ToggleDirectionMenuItem direction={direction} setDirection={setDirection} />
      {hasMultipleGroups && expandedGroups && allGroups && setExpandedGroups ? (
        <ToggleGroupsMenuItem
          expandedGroups={expandedGroups}
          setExpandedGroups={setExpandedGroups}
          allGroups={allGroups}
        />
      ) : null}
      {setHideEdgesToNodesOutsideQuery ? (
        <ToggleHideEdgesToNodesOutsideQueryMenuItem
          hideEdgesToNodesOutsideQuery={hideEdgesToNodesOutsideQuery}
          setHideEdgesToNodesOutsideQuery={setHideEdgesToNodesOutsideQuery}
        />
      ) : null}
      <ToggleShowStubAssetsMenuItem />
    </Menu>
  );
};

export const ToggleGroupsMenuItem = ({
  expandedGroups,
  setExpandedGroups,
  allGroups,
}: {
  expandedGroups: string[];
  setExpandedGroups: (v: string[]) => void;
  allGroups: string[];
}) => (
  <MenuItem
    icon={expandedGroups.length === 0 ? <Icon name="unfold_more" /> : <Icon name="unfold_less" />}
    onClick={() => setExpandedGroups(expandedGroups.length === 0 ? allGroups : [])}
    text={
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        {expandedGroups.length === 0 ? 'Expand all groups' : 'Collapse all groups'}{' '}
        <KeyboardTag>⌥E</KeyboardTag>
      </Box>
    }
  />
);

export const useLayoutDirectionState = () =>
  useStateWithStorage<AssetLayoutDirection>('asset-graph-direction', (json) =>
    ['vertical', 'horizontal'].includes(json) ? json : 'horizontal',
  );

export const ToggleDirectionMenuItem = ({
  direction,
  setDirection,
}: {
  direction: AssetLayoutDirection;
  setDirection: (d: AssetLayoutDirection) => void;
}) => (
  <MenuItem
    icon={
      direction === 'horizontal' ? <Icon name="graph_vertical" /> : <Icon name="graph_horizontal" />
    }
    onClick={() => setDirection(direction === 'vertical' ? 'horizontal' : 'vertical')}
    text={
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        Change graph to {direction === 'vertical' ? 'horizontal' : 'vertical'} orientation{' '}
        <KeyboardTag>⌥O</KeyboardTag>
      </Box>
    }
  />
);

export const ToggleHideEdgesToNodesOutsideQueryMenuItem = ({
  hideEdgesToNodesOutsideQuery,
  setHideEdgesToNodesOutsideQuery,
}: {
  hideEdgesToNodesOutsideQuery?: boolean;
  setHideEdgesToNodesOutsideQuery: (hideEdgesToNodesOutsideQuery: boolean) => void;
}) => {
  return (
    <MenuItem
      icon={
        hideEdgesToNodesOutsideQuery ? <Icon name="visibility" /> : <Icon name="visibility_off" />
      }
      onClick={() => setHideEdgesToNodesOutsideQuery(!hideEdgesToNodesOutsideQuery)}
      text={
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          {hideEdgesToNodesOutsideQuery ? 'Show' : 'Hide'} neighbor assets outside of selection{' '}
          <KeyboardTag>⌥V</KeyboardTag>
        </Box>
      }
    />
  );
};

export const ToggleShowStubAssetsMenuItem = () => {
  const {showStubAssets, setShowStubAssets} = useShowStubAssets();

  return (
    <MenuItem
      icon={showStubAssets ? <Icon name="visibility" /> : <Icon name="visibility_off" />}
      onClick={() => setShowStubAssets(!showStubAssets)}
      text={
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Body>{showStubAssets ? 'Hide' : 'Show'} stub assets </Body>
          <div style={{marginLeft: 8}}>
            <Tooltip content="Stub assets are placeholder assets that Dagster automatically creates to represent dependencies that aren't defined in your current code location. ">
              <Icon name="info" />
            </Tooltip>
          </div>
          <KeyboardTag>⌥S</KeyboardTag>
        </Box>
      }
    />
  );
};

const ProductTourWrapper = ({children}: {children: React.ReactNode}) => {
  const [hideNeighborAssetsNux, setHideNeighborAssetsNux] = useStateWithStorage<any>(
    'AssetGraphHideNeighborAssetsNux',
    (value) => value,
  );
  if (hideNeighborAssetsNux) {
    return children;
  }
  return (
    <ProductTour
      title="Show and hide neighboring assets outside of selection"
      description={
        <>
          You can show and hide neighboring assets outside of your selection by right clicking on
          the graph and selecting the show/hide neighboring assets option.
        </>
      }
      position={ProductTourPosition.BOTTOM_RIGHT}
      video={ShowAndHideNeighborAssetsMP4}
      width="616px"
      actions={{
        dismiss: () => {
          setHideNeighborAssetsNux('1');
        },
      }}
    >
      {children}
    </ProductTour>
  );
};
