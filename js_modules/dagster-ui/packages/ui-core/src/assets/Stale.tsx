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
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {LiveDataForNode, displayNameForAssetKey} from '../asset-graph/Utils';
import {AssetNodeKeyFragment} from '../asset-graph/types/AssetNode.types';
import {AssetKeyInput, ChangeReason, StaleCauseCategory, StaleStatus} from '../graphql/types';
import {numberFormatter} from '../ui/formatters';

type StaleDataForNode = Pick<LiveDataForNode, 'staleCauses' | 'staleStatus' | 'changedReasons'>;

export const isAssetMissing = (liveData?: Pick<StaleDataForNode, 'staleStatus'>) =>
  liveData && liveData.staleStatus === StaleStatus.MISSING;

export const isAssetStale = (liveData?: Pick<StaleDataForNode, 'staleStatus'>) =>
  liveData && liveData.staleStatus === StaleStatus.STALE;

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
  include,
  assetKey,
}: {
  assetKey: AssetKeyInput;
  include: 'all' | 'upstream' | 'self';
  liveData?: StaleDataForNode;
}) => {
  if (!isAssetStale(liveData) || !liveData?.staleCauses.length) {
    return null;
  }

  return (
    <Body color={Colors.textYellow()}>
      <Popover
        position="top"
        content={
          <StaleCausesPopoverSummary liveData={liveData} assetKey={assetKey} include={include} />
        }
        interactionKind="hover"
        className="chunk-popover-target"
      >
        {Object.keys(groupedCauses(assetKey, include, liveData)).join(', ')}
      </Popover>
    </Body>
  );
};

export const StaleReasonsTag = ({
  assetKey,
  liveData,
  include = 'all',
  onClick,
}: {
  assetKey: AssetKeyInput;
  liveData?: StaleDataForNode;
  include?: 'all' | 'upstream' | 'self';
  onClick?: () => void;
}) => {
  const staleTag = useMemo(() => {
    if (!isAssetStale(liveData) || !liveData?.staleCauses.length) {
      return <div />;
    }
    const label = (
      <Caption>Outdated ({numberFormatter.format(liveData.staleCauses.length)})</Caption>
    );
    return (
      <Popover
        content={
          <StaleCausesPopoverSummary liveData={liveData} assetKey={assetKey} include={include} />
        }
        position="top"
        interactionKind="hover"
        className="chunk-popover-target"
      >
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
      </Popover>
    );
  }, [assetKey, include, liveData, onClick]);

  const isNew = liveData?.changedReasons?.includes(ChangeReason.NEW);

  return (
    <Box
      flex={{gap: 4, alignItems: 'center', justifyContent: 'space-between'}}
      padding={{horizontal: 4}}
      style={{height: 24}}
    >
      {staleTag}
      {isNew ? (
        <NewInBranchTag changedReasons={liveData!.changedReasons!} assetKey={assetKey} />
      ) : null}
    </Box>
  );
};

function groupedCauses(
  assetKey: AssetKeyInput,
  include: 'all' | 'upstream' | 'self',
  liveData?: StaleDataForNode,
) {
  const all = (liveData?.staleCauses || [])
    .map((cause) => {
      const target = isEqual(assetKey.path, cause.key.path) ? 'self' : 'upstream';
      return {...cause, target, label: LABELS[target][cause.category]};
    })
    .filter((cause) => include === 'all' || include === cause.target);

  return groupBy(all, (cause) => cause.label);
}

const StaleCausesPopoverSummary = ({
  assetKey,
  liveData,
  include,
}: {
  assetKey: AssetKeyInput;
  liveData?: StaleDataForNode;
  include: 'all' | 'upstream' | 'self';
}) => {
  const grouped = groupedCauses(assetKey, include, liveData);
  const totalCauses = liveData?.staleCauses.length;

  if (!totalCauses) {
    // Should never happen since the parent of this component should check that the asset is stale before rendering the popover
    return <div />;
  }
  return (
    <Box flex={{direction: 'column'}}>
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
              <StaleReason key={idx} reason={cause.reason} dependency={cause.dependency} />
            ))}
          </Box>
        );
      })}
    </Box>
  );
};

const StaleReason = ({
  reason,
  dependency,
}: {
  reason: string;
  dependency: AssetNodeKeyFragment | null;
}) => {
  const content = useMemo(() => {
    if (!dependency) {
      return <Caption>{` ${reason}`}</Caption>;
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
  }, [dependency, reason]);
  return (
    <Box
      padding={{vertical: 8, horizontal: 12}}
      flex={{direction: 'row', alignItems: 'center', gap: 4}}
    >
      {content}
    </Box>
  );
};

export const NewInBranchTag = ({
  changedReasons,
  assetKey,
}: {
  changedReasons: ChangeReason[];
  assetKey: AssetKeyInput;
}) => {
  const changes = changedReasons.filter((reason) => reason !== ChangeReason.NEW);

  function getDescription(change: ChangeReason) {
    switch (change) {
      case ChangeReason.NEW:
        return '';
      case ChangeReason.CODE_VERSION:
        return 'has a modified code version';
      case ChangeReason.INPUTS:
        return 'has modified dependencies';
      case ChangeReason.PARTITIONS_DEFINITION:
        return 'has a modified partition definition';
    }
  }
  return (
    <Popover
      position="top"
      content={
        <Box flex={{direction: 'column'}}>
          <Box padding={{horizontal: 12, vertical: 8}} border="bottom">
            <Subtitle2>
              {numberFormatter.format(changes.length)}{' '}
              {ifPlural(changes.length, 'change', 'changes')} in this branch
            </Subtitle2>
          </Box>
          {changes.map((change) => {
            return (
              <Box
                key={change}
                padding={{vertical: 8, horizontal: 12}}
                flex={{direction: 'row', alignItems: 'center', gap: 4}}
              >
                <Tag icon="asset">{displayNameForAssetKey(assetKey)}</Tag>
                {getDescription(change)}
              </Box>
            );
          })}
        </Box>
      }
      interactionKind="hover"
      className="chunk-popover-target"
    >
      <BaseTag
        fillColor={Colors.backgroundCyan()}
        textColor={Colors.textCyan()}
        label="New in branch"
        icon={<Icon name="new_in_branch" color={Colors.accentCyan()} />}
      />
    </Popover>
  );
};
