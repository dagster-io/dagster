import {Box, Colors, FontFamily, Icon, Tooltip} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled, {CSSObject} from 'styled-components';

import {ASSET_NODE_HOVER_EXPAND_HEIGHT} from './AssetNode2025';
import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {AssetNodeHealthRow} from './AssetNodeHealthRow';
import {AssetNodeMenuProps, useAssetNodeMenu} from './AssetNodeMenu';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {LiveDataForNode} from './Utils';
import {
  ASSET_NODE_NAME_MAX_LENGTH,
  ASSET_NODE_STATUS_ROW_HEIGHT,
  ASSET_NODE_TAGS_HEIGHT,
} from './layout';
import {gql} from '../apollo-client';
import {AssetNodeFragment} from './types/AssetNode.types';
import {withMiddleTruncation} from '../app/Util';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {statusToIconAndColor} from '../assets/AssetHealthSummary';
import {PartitionCountTags} from '../assets/AssetNodePartitionCounts';
import {ChangedReasonsTag, MinimalNodeChangedDot} from '../assets/ChangedReasons';
import {MinimalNodeStaleDot, StaleReasonsTag, isAssetStale} from '../assets/Stale';
import {AssetChecksStatusSummary} from '../assets/asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKind} from '../graph/KindTags';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';

interface Props {
  definition: AssetNodeFragment;
  selected: boolean;
  onChangeAssetSelection?: (selection: string) => void;
}

export const AssetNode = React.memo(({definition, selected, onChangeAssetSelection}: Props) => {
  const {liveData} = useAssetLiveData(definition.assetKey);
  const hasChecks = (liveData?.assetChecks || []).length > 0;

  const marginTopForCenteringNode = !hasChecks ? ASSET_NODE_STATUS_ROW_HEIGHT / 2 : 0;

  return (
    <AssetNodeContainer $selected={selected}>
      <Box
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        style={{minHeight: ASSET_NODE_TAGS_HEIGHT, marginTop: marginTopForCenteringNode}}
      >
        <div>
          <StaleReasonsTag liveData={liveData} assetKey={definition.assetKey} />
        </div>
        <ChangedReasonsTag
          changedReasons={definition.changedReasons}
          assetKey={definition.assetKey}
        />
      </Box>
      <AssetNodeBox $selected={selected} $isMaterializable={definition.isMaterializable}>
        <AssetNameRow definition={definition} />
        <Box style={{padding: '6px 8px'}} flex={{direction: 'column', gap: 4}} border="top">
          {definition.description ? (
            <AssetDescription $color={Colors.textDefault()}>
              {markdownToPlaintext(definition.description).split('\n')[0]}
            </AssetDescription>
          ) : (
            <AssetDescription $color={Colors.textLight()}>No description</AssetDescription>
          )}
          {definition.isPartitioned && definition.isMaterializable && (
            <PartitionCountTags definition={definition} liveData={liveData} />
          )}
        </Box>
        <AssetNodeHealthRow definition={definition} liveData={liveData} />

        {hasChecks && <AssetNodeChecksRow definition={definition} liveData={liveData} />}
      </AssetNodeBox>
      <Box
        style={{minHeight: ASSET_NODE_TAGS_HEIGHT}}
        flex={{alignItems: 'center', direction: 'row-reverse', gap: 8}}
      >
        {definition.kinds.map((kind) => (
          <AssetKind
            key={kind}
            kind={kind}
            style={{position: 'relative', margin: 0}}
            onChangeAssetSelection={onChangeAssetSelection}
          />
        ))}
      </Box>
    </AssetNodeContainer>
  );
}, isEqual);

export const AssetNameRow = ({definition}: {definition: AssetNodeFragment}) => {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1]!;

  return (
    <AssetName $isMaterializable={definition.isMaterializable}>
      <span style={{marginTop: 1}}>
        <Icon name={definition.isMaterializable ? 'asset' : 'source_asset'} />
      </span>
      <div
        data-tooltip={displayName}
        data-tooltip-style={definition.isMaterializable ? NameTooltipStyle : NameTooltipStyleSource}
        style={{overflow: 'hidden', textOverflow: 'ellipsis'}}
      >
        {withMiddleTruncation(displayName, {
          maxLength: ASSET_NODE_NAME_MAX_LENGTH,
        })}
      </div>
      <div style={{flex: 1}} />
    </AssetName>
  );
};

export const AssetNodeRowBox = styled(Box)`
  white-space: nowrap;
  line-height: 12px;
  font-size: 12px;
  height: 24px;
  a:hover {
    text-decoration: none;
  }
  &:last-child {
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
  }
`;

export const AssetNodeContextMenuWrapper = React.memo(
  ({children, ...menuProps}: AssetNodeMenuProps & {children: React.ReactNode}) => {
    const {dialog, menu} = useAssetNodeMenu(menuProps);
    return (
      <>
        <ContextMenuWrapper menu={menu} stopPropagation>
          {children}
        </ContextMenuWrapper>
        {dialog}
      </>
    );
  },
);

const AssetNodeChecksRow = ({
  definition,
  liveData,
}: {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}) => {
  if (!liveData || !liveData.assetChecks.length) {
    return <span />;
  }

  return (
    <AssetNodeRowBox
      padding={{horizontal: 8}}
      flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
      border="top"
      background={Colors.backgroundLight()}
    >
      Checks
      <Link
        to={assetDetailsPathForKey(definition.assetKey, {view: 'checks'})}
        onClick={(e) => e.stopPropagation()}
      >
        <AssetChecksStatusSummary
          liveData={liveData}
          rendering="dag"
          assetKey={definition.assetKey}
        />
      </Link>
    </AssetNodeRowBox>
  );
};

type AssetNodeMinimalProps = {
  selected: boolean;
  definition: AssetNodeFragment;
  facets: Set<AssetNodeFacet> | null;
  height: number;
};

export const AssetNodeMinimal = ({definition, facets, height, selected}: AssetNodeMinimalProps) => {
  const {isMaterializable, assetKey} = definition;
  const {liveData} = useAssetLiveData(assetKey);
  const {liveData: healthData} = useAssetHealthData(assetKey);
  const health = healthData?.assetHealth;

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const displayName = assetKey.path[assetKey.path.length - 1]!;
  const isChanged = definition.changedReasons.length;
  const isStale = isAssetStale(liveData);

  const queuedRuns = liveData?.unstartedRunIds.length;
  const inProgressRuns = liveData?.inProgressRunIds.length;
  const numMaterializing = liveData?.partitionStats?.numMaterializing;
  const isMaterializing = numMaterializing || inProgressRuns || queuedRuns;

  const {borderColor, backgroundColor} = React.useMemo(() => {
    if (isMaterializing) {
      return {backgroundColor: Colors.backgroundBlue(), borderColor: Colors.accentBlue()};
    }
    return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
  }, [health, isMaterializing]);

  // old design
  let paddingTop = height / 2 - 52;
  let nodeHeight = 86;

  if (facets !== null) {
    const topTagsPresent = facets.has(AssetNodeFacet.UnsyncedTag);
    const bottomTagsPresent = facets.has(AssetNodeFacet.KindTag);
    paddingTop = ASSET_NODE_VERTICAL_MARGIN + (topTagsPresent ? ASSET_NODE_TAGS_HEIGHT : 0);
    nodeHeight =
      height -
      ASSET_NODE_VERTICAL_MARGIN * 2 -
      (topTagsPresent ? ASSET_NODE_TAGS_HEIGHT : ASSET_NODE_HOVER_EXPAND_HEIGHT) -
      (bottomTagsPresent ? ASSET_NODE_TAGS_HEIGHT : 0);

    // Ensure that we have room for the label, even if it makes the minimal format larger.
    if (nodeHeight < 38) {
      nodeHeight = 38;
    }
  }

  return (
    <MinimalAssetNodeContainer $selected={selected} style={{paddingTop}}>
      <TooltipStyled
        content={displayName}
        canShow={displayName.length > 14}
        targetTagName="div"
        position="top"
      >
        <MinimalAssetNodeBox
          $selected={selected}
          $isMaterializable={isMaterializable}
          $background={backgroundColor}
          $border={borderColor}
          $inProgress={!!inProgressRuns}
          $isQueued={!!queuedRuns}
          $height={nodeHeight}
        >
          {isChanged ? (
            <MinimalNodeChangedDot changedReasons={definition.changedReasons} assetKey={assetKey} />
          ) : null}
          {isStale ? <MinimalNodeStaleDot assetKey={assetKey} liveData={liveData} /> : null}
          <MinimalName style={{fontSize: 24}} $isMaterializable={isMaterializable}>
            {withMiddleTruncation(displayName, {maxLength: 18})}
          </MinimalName>
        </MinimalAssetNodeBox>
      </TooltipStyled>
    </MinimalAssetNodeContainer>
  );
};

// Note: This fragment should only contain fields that are needed for
// useAssetGraphData and the Asset DAG. Some pages of Dagster UI request this
// fragment for every AssetNode on the instance. Add fields with care!
//
export const ASSET_NODE_FRAGMENT = gql`
  fragment AssetNodeFragment on AssetNode {
    id
    graphName
    hasMaterializePermission
    jobNames
    changedReasons
    opNames
    opVersion
    description
    computeKind
    isPartitioned
    isObservable
    isMaterializable
    isAutoCreatedStub
    owners {
      ... on TeamAssetOwner {
        team
      }
      ... on UserAssetOwner {
        email
      }
    }
    assetKey {
      ...AssetNodeKey
    }
    tags {
      key
      value
    }
    kinds
  }

  fragment AssetNodeKey on AssetKey {
    path
  }
`;

export const ASSET_NODE_VERTICAL_MARGIN = 6;

export const AssetNodeContainer = styled.div<{$selected: boolean}>`
  user-select: none;
  cursor: pointer;

  & *:focus {
    outline: 0;
  }
`;

const AssetNodeShowOnHover = styled.span`
  display: none;
`;

export const AssetNodeBox = styled.div<{
  $isMaterializable: boolean;
  $selected: boolean;
  $noScale?: boolean;
}>`
  ${(p) =>
    !p.$isMaterializable
      ? `border: 2px dashed ${p.$selected ? Colors.accentGrayHover() : Colors.accentGray()}`
      : `border: 2px solid ${
          p.$selected ? Colors.lineageNodeBorderSelected() : Colors.lineageNodeBorder()
        }`};
  ${(p) => p.$selected && `outline: 2px solid ${Colors.lineageNodeBorderSelected()}`};

  background: ${Colors.backgroundDefault()};
  border-radius: 10px;
  position: relative;
  margin: ${ASSET_NODE_VERTICAL_MARGIN}px 0;
  transition: all 150ms linear;
  &:hover {
    ${(p) => !p.$selected && `border: 2px solid ${Colors.lineageNodeBorderHover()};`};
    box-shadow: ${Colors.shadowDefault()} 0px 1px 4px 0px;
    scale: ${(p) => (p.$noScale ? '1' : '1.03')};
    ${AssetNodeShowOnHover} {
      display: initial;
    }
  }
`;

/** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
const NameCSS: CSSObject = {
  padding: '3px 0 3px 6px',
  color: Colors.textDefault(),
  fontSize: 14,
  fontFamily: FontFamily.monospace,
  fontWeight: 600,
};

export const NameTooltipCSS: CSSObject = {
  ...NameCSS,
  top: -9,
  left: -12,
  fontSize: 14,
};

export const NameTooltipStyle = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.lineageNodeBackground(),
  border: `none`,
});

const NameTooltipStyleSource = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.backgroundLight(),
  border: `none`,
});

const AssetName = styled.div<{$isMaterializable: boolean}>`
  ${NameCSS};
  display: flex;
  gap: 4px;
  background: ${(p) =>
    p.$isMaterializable ? Colors.lineageNodeBackground() : Colors.backgroundLight()};
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
`;

const MinimalAssetNodeContainer = styled(AssetNodeContainer)`
  height: 100%;
`;

const MinimalAssetNodeBox = styled.div<{
  $isMaterializable: boolean;
  $selected: boolean;
  $background: string;
  $border: string;
  $inProgress: boolean;
  $isQueued: boolean;
  $height: number;
}>`
  background: ${(p) => p.$background};
  overflow: hidden;
  ${(p) =>
    !p.$isMaterializable
      ? `border: 4px dashed ${p.$selected ? Colors.accentGray() : p.$border}`
      : `border: 4px solid ${p.$selected ? Colors.lineageNodeBorderSelected() : p.$border}`};
  ${(p) =>
    p.$inProgress
      ? `
      background-color: ${p.$background};
      &::after {
        inset: 0;
        position: absolute;
        transform: translateX(-100%);
        mask-image: linear-gradient(90deg, rgba(255,255,255,0) 0, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3));
        background: ${p.$background};
        animation: shimmer 1.5s infinite;
        content: '';
      }

      @keyframes shimmer {
        100% {
          transform: translateX(100%);
        }
      }
  `
      : ''}

  ${(p) =>
    p.$isQueued
      ? `
      border: none;
      &::after {
        inset: 0;
        position: absolute;
        animation: pulse 0.75s infinite alternate;
        border-radius: 16px;
        border: 4px solid ${p.$border};
        content: '';
      }
      @keyframes pulse {
        0% {
          opacity: 0.2;
        }
        100% {
          opacity: 1;
        }
      }
      `
      : ''}
  border-radius: 16px;
  position: relative;
  padding: 2px;
  height: ${(p) => p.$height}px;
  &:hover {
    box-shadow: ${Colors.shadowDefault()} 0px 2px 12px 0px;
  }
`;

const MinimalName = styled(AssetName)`
  font-weight: 600;
  white-space: nowrap;
  position: absolute;
  background: none;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
`;

export const AssetDescription = styled.div<{$color: string}>`
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: ${(p) => p.$color};
  font-size: 12px;
`;

const TooltipStyled = styled(Tooltip)`
  height: 100%;
`;
