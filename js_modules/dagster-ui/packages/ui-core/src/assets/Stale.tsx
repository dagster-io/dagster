import {
  BaseTag,
  Body,
  Box,
  ButtonLink,
  Caption,
  CaptionSubtitle,
  Colors,
  Icon,
  Popover,
  Subtitle2,
  Tag,
  ifPlural,
} from '@dagster-io/ui-components';
import groupBy from 'lodash/groupBy';
import isEqual from 'lodash/isEqual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetStaleDataFragment} from '../asset-data/types/AssetStaleStatusDataProvider.types';
import {LiveDataForNode, displayNameForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput, StaleCauseCategory, StaleStatus} from '../graphql/types';
import {numberFormatter} from '../ui/formatters';

type StaleDataForNode = {
  staleCauses: AssetStaleDataFragment['staleCauses'];
  staleStatus: AssetStaleDataFragment['staleStatus'];

  // May be omitted when showing staleness for a single partition
  partitionStats?: LiveDataForNode['partitionStats'];
};

export const isAssetMissing = (
  liveData?: Pick<StaleDataForNode, 'staleStatus' | 'partitionStats'>,
) => {
  if (!liveData) {
    return false;
  }
  const {partitionStats, staleStatus} = liveData;

  return partitionStats
    ? partitionStats.numPartitions -
        partitionStats.numMaterializing -
        partitionStats.numMaterialized >
        0
    : staleStatus === StaleStatus.MISSING;
};

export const isAssetStale = (liveData?: Pick<StaleDataForNode, 'staleStatus'>) => {
  return liveData && liveData.staleStatus === StaleStatus.STALE;
};

const LABELS = {
  self: {
    [StaleCauseCategory.CODE]: 'Code version',
    [StaleCauseCategory.DATA]: 'Data version',
    [StaleCauseCategory.DEPENDENCIES]: 'Dependencies',
  },
  upstream: {
    [StaleCauseCategory.CODE]: 'Upstream code version',
    [StaleCauseCategory.DATA]: 'Upstream data',
    [StaleCauseCategory.DEPENDENCIES]: 'Upstream dependencies',
  },
};

function getCollapsedHeaderLabel(isSelf: boolean, category: StaleCauseCategory, count: number) {
  const upstreamString = isSelf ? ' ' : ' upstream ';
  switch (category) {
    case StaleCauseCategory.CODE:
      if (count === 1) {
        return `1${upstreamString}code version change`;
      } else {
        return `${count}${upstreamString}code version changes`;
      }
    case StaleCauseCategory.DATA:
      if (count === 1) {
        return `1${upstreamString}data version change`;
      } else {
        return `${count}${upstreamString}data version changes`;
      }
    case StaleCauseCategory.DEPENDENCIES:
      if (count === 1) {
        return `1${upstreamString}dependency change`;
      } else {
        return `${count}${upstreamString}dependency changes`;
      }
  }
}

export const StaleReasonsLabel = ({
  liveData,
  assetKey,
}: {
  assetKey: AssetKeyInput;
  liveData?: StaleDataForNode;
}) => {
  if (!isAssetStale(liveData)) {
    return null;
  }

  return (
    <Body color={Colors.textYellow()}>
      <Popover
        position="top"
        content={<StaleCausesPopoverSummary liveData={liveData} assetKey={assetKey} />}
        interactionKind="hover"
        className="chunk-popover-target"
      >
        {Object.keys(groupedCauses(assetKey, liveData)).join(', ')}
      </Popover>
    </Body>
  );
};

// Includes the cha
export const StaleReasonsTag = ({
  assetKey,
  liveData,
  onClick,
}: {
  assetKey: AssetKeyInput;
  liveData?: StaleDataForNode;
  onClick?: () => void;
}) => {
  const grouped = groupedCauses(assetKey, liveData);
  const totalCauses = Object.values(grouped).reduce((s, g) => s + g.length, 0);
  if (!totalCauses) {
    return <div />;
  }
  const label = <Caption>Unsynced ({numberFormatter.format(totalCauses)})</Caption>;
  return (
    <Box
      flex={{gap: 4, alignItems: 'center', justifyContent: 'space-between'}}
      padding={{horizontal: 4}}
      style={{height: 24}}
    >
      <StaleCausesPopover assetKey={assetKey} liveData={liveData}>
        <BaseTag
          fillColor={Colors.backgroundYellow()}
          textColor={Colors.textYellow()}
          icon={<Icon name="changes_present" color={Colors.textYellow()} />}
          label={
            onClick ? (
              <ButtonLink underline="never" onClick={onClick} color={Colors.textYellow()}>
                {label}
              </ButtonLink>
            ) : (
              label
            )
          }
        />
      </StaleCausesPopover>
    </Box>
  );
};

export const StaleCausesPopover = ({
  liveData,
  assetKey,
  children,
}: {
  assetKey: AssetKeyInput;
  liveData?: StaleDataForNode;
  children: React.ReactNode;
}) => {
  return (
    <Popover
      content={<StaleCausesPopoverSummary liveData={liveData} assetKey={assetKey} />}
      position="top-left"
      interactionKind="hover"
      className="chunk-popover-target"
    >
      {children}
    </Popover>
  );
};

function groupedCauses(assetKey: AssetKeyInput, liveData?: StaleDataForNode) {
  const all = (liveData?.staleCauses || []).map((cause) => {
    const target = isEqual(assetKey.path, cause.key.path) ? 'self' : 'upstream';
    return {...cause, target, label: LABELS[target][cause.category]};
  });

  return groupBy(all, (cause) => cause.label);
}

const StaleCausesPopoverSummary = ({
  assetKey,
  liveData,
}: {
  assetKey: AssetKeyInput;
  liveData?: StaleDataForNode;
}) => {
  const grouped = groupedCauses(assetKey, liveData);
  const totalCauses = Object.values(grouped).reduce((s, g) => s + g.length, 0);

  if (!totalCauses) {
    // Can happen if the parent didn't checked the grouped causes
    return <div />;
  }
  return (
    <Box flex={{direction: 'column'}} style={{maxHeight: 300, overflowY: 'auto'}}>
      <Box padding={{horizontal: 12, vertical: 8}} border="bottom">
        <Subtitle2>
          {numberFormatter.format(totalCauses)} {ifPlural(totalCauses, 'change', 'changes')} since
          last materialization
        </Subtitle2>
      </Box>
      {Object.entries(grouped).map(([label, causes], idx) => {
        const isSelf = isEqual(assetKey.path, causes[0]!.key.path);
        return (
          <Box key={label}>
            <Box
              padding={{horizontal: 12, vertical: 8}}
              border={idx === 0 ? 'bottom' : 'top-and-bottom'}
            >
              <CaptionSubtitle>
                {getCollapsedHeaderLabel(isSelf, causes[0]!.category, causes.length)}
              </CaptionSubtitle>
            </Box>
            {causes.map((cause, idx) => (
              <Box
                padding={{vertical: 8, horizontal: 12}}
                flex={{direction: 'row', alignItems: 'center', gap: 4}}
                key={idx}
              >
                <StaleReason cause={cause} />
              </Box>
            ))}
          </Box>
        );
      })}
    </Box>
  );
};

const StaleReason = ({cause}: {cause: NonNullable<StaleDataForNode['staleCauses']>[0]}) => {
  const {dependency, reason, key} = cause;
  if (!dependency) {
    return (
      <>
        <Link to={assetDetailsPathForKey(key)}>
          <Tag icon="asset">{displayNameForAssetKey(key)}</Tag>
        </Link>
        <Caption>{` ${reason}`}</Caption>
      </>
    );
  }

  const dependencyName = displayNameForAssetKey(dependency);
  const dependencyPythonName = dependencyName.replace(/ /g, '');
  if (reason.endsWith(`${dependencyPythonName}`)) {
    const reasonUpToDep = reason.slice(0, -dependencyPythonName.length);
    return (
      <>
        <Caption>{reasonUpToDep}</Caption>
        <Link to={assetDetailsPathForKey(dependency)}>
          <Tag icon="asset">{dependencyName}</Tag>
        </Link>
      </>
    );
  }

  return (
    <>
      <Link to={assetDetailsPathForKey(dependency)}>
        <Tag icon="asset">{dependencyName}</Tag>
      </Link>
      <Caption>{` ${reason} `}</Caption>
    </>
  );
};

export const MinimalNodeStaleDot = ({
  liveData,
  assetKey,
}: {
  liveData?: StaleDataForNode;
  assetKey: AssetKeyInput;
}) => {
  return (
    <StaleCausesPopover liveData={liveData} assetKey={assetKey}>
      <MinimalNodeStaleDotElement />
    </StaleCausesPopover>
  );
};

const MinimalNodeStaleDotElement = styled.div`
  position: absolute;
  left: 6px;
  top: 6px;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background-color: ${Colors.backgroundYellow()};
  &:after {
    display: block;
    position: absolute;
    content: ' ';
    left: 5px;
    top: 5px;
    height: 10px;
    width: 10px;
    border-radius: 50%;
    background-color: ${Colors.accentYellow()};
  }
`;
