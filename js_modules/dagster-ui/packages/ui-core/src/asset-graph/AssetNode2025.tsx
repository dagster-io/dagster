import {Box, Colors, Icon, Tag} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {ChangedReasonsTag} from '../assets/ChangedReasons';
import {StaleReasonsTag} from '../assets/Stale';
import {AssetChecksStatusSummary} from '../assets/asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKind} from '../graph/KindTags';
import {
  AssetDescription,
  AssetInsetForHoverEffect,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
} from './AssetNode';
import {labelForFacet} from './AssetNodeFacets';
import {assetNodeLatestEventContent, buildAssetNodeStatusContent} from './AssetNodeStatusContent';
import {LiveDataForNode} from './Utils';
import {ASSET_NODE_TAGS_HEIGHT} from './layout';
import {AssetNodeFragment} from './types/AssetNode.types';
import {isAssetOverdue} from 'shared/assets/OverdueTag';
import {AssetNodeFacet} from './AssetNodeFacets';
import {markdownToPlaintext} from 'shared/ui/markdownToPlaintext';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';

interface Props2025 {
  definition: AssetNodeFragment;
  selected: boolean;
  facets: Set<AssetNodeFacet>;
  onChangeAssetSelection?: (selection: string) => void;
}

const HOVER_EXPAND_MARGIN = 3;

export const AssetNode2025 = React.memo(
  ({definition, selected, facets, onChangeAssetSelection}: Props2025) => {
    const {liveData} = useAssetLiveData(definition.assetKey);

    return (
      <AssetInsetForHoverEffect>
        <AssetNodeContainer $selected={selected}>
          {facets.has(AssetNodeFacet.UnsyncedTag) ? (
            <Box
              flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
              style={{minHeight: ASSET_NODE_TAGS_HEIGHT}}
            >
              <StaleReasonsTag liveData={liveData} assetKey={definition.assetKey} />
              <ChangedReasonsTag
                changedReasons={definition.changedReasons}
                assetKey={definition.assetKey}
              />
            </Box>
          ) : (
            <div style={{minHeight: HOVER_EXPAND_MARGIN}} />
          )}
          <AssetNodeBox $selected={selected} $isMaterializable={definition.isMaterializable}>
            <AssetNameRow definition={definition} />
            {facets.has(AssetNodeFacet.Description) && (
              <AssetNodeRow label={null}>
                {definition.description ? (
                  <AssetDescription $color={Colors.textDefault()}>
                    {markdownToPlaintext(definition.description).split('\n')[0]}
                  </AssetDescription>
                ) : (
                  <AssetDescription $color={Colors.textDefault()}>No description</AssetDescription>
                )}
              </AssetNodeRow>
            )}
            {facets.has(AssetNodeFacet.Owner) && (
              <AssetNodeRow label={labelForFacet(AssetNodeFacet.Owner)}>
                {definition.owners.length > 0
                  ? definition.owners.map((owner, idx) =>
                      owner.__typename === 'UserAssetOwner' ? (
                        <UserDisplayWrapNoPadding key={idx}>
                          <UserDisplay email={owner.email} size="very-small" />
                        </UserDisplayWrapNoPadding>
                      ) : (
                        <Tag icon="people" key={idx}>
                          {owner.team}
                        </Tag>
                      ),
                    )
                  : null}
              </AssetNodeRow>
            )}
            {facets.has(AssetNodeFacet.LatestEvent) && (
              <AssetNodeRow label={labelForFacet(AssetNodeFacet.LatestEvent)}>
                {assetNodeLatestEventContent({definition, liveData})}
              </AssetNodeRow>
            )}
            {facets.has(AssetNodeFacet.Checks) && (
              <AssetNodeRow label={labelForFacet(AssetNodeFacet.Checks)}>
                {liveData && liveData.assetChecks.length > 0 ? (
                  <Link
                    to={assetDetailsPathForKey(definition.assetKey, {view: 'checks'})}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <AssetChecksStatusSummary
                      liveData={liveData}
                      rendering="dag2025"
                      assetKey={definition.assetKey}
                    />
                  </Link>
                ) : null}
              </AssetNodeRow>
            )}
            {facets.has(AssetNodeFacet.Freshness) && (
              <AssetNodeRow label={labelForFacet(AssetNodeFacet.Freshness)}>
                {!liveData?.freshnessInfo ? null : isAssetOverdue(liveData) ? (
                  <Box flex={{gap: 4, alignItems: 'center'}}>
                    <Icon name="close" color={Colors.accentRed()} />
                    Violated
                  </Box>
                ) : (
                  <Box flex={{gap: 4, alignItems: 'center'}}>
                    <Icon name="done" color={Colors.accentGreen()} />
                    Passing
                  </Box>
                )}
              </AssetNodeRow>
            )}
            {facets.has(AssetNodeFacet.Status) && (
              <AssetNodeStatusRow definition={definition} liveData={liveData} />
            )}
          </AssetNodeBox>
          {facets.has(AssetNodeFacet.KindTag) && (
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
          )}
        </AssetNodeContainer>
      </AssetInsetForHoverEffect>
    );
  },
  isEqual,
);

const AssetNodeRowBox = styled(Box)`
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

const AssetNodeRow = ({
  label,
  children,
}: {
  label: string | null;
  children: React.ReactNode | null;
}) => {
  return (
    <AssetNodeRowBox
      padding={{horizontal: 8}}
      flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
      border={'bottom'}
    >
      {label ? <span style={{color: Colors.textLight()}}>{label}</span> : undefined}
      {children ? children : <span style={{color: Colors.textLighter()}}>–</span>}
    </AssetNodeRowBox>
  );
};

interface StatusRowProps {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}

const AssetNodeStatusRow = ({definition, liveData}: StatusRowProps) => {
  const {content, background} = buildAssetNodeStatusContent({
    assetKey: definition.assetKey,
    definition,
    liveData,
  });
  return (
    <AssetNodeRowBox
      background={background}
      padding={{horizontal: 8}}
      flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
    >
      {content}
    </AssetNodeRowBox>
  );
};

const UserDisplayWrapNoPadding = styled.div`
  & > div > div {
    background: none;
    padding: 0;
  }
`;
