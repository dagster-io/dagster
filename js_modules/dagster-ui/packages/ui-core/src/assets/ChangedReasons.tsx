import {
  BaseTag,
  Box,
  Colors,
  Icon,
  Popover,
  Subtitle2,
  Tag,
  ifPlural,
} from '@dagster-io/ui-components';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import styles from './css/ChangedReasons.module.css';
import {AssetKeyInput, ChangeReason} from '../graphql/types';
import {numberFormatter} from '../ui/formatters';

export const ChangedReasonsTag = ({
  changedReasons,
  assetKey,
}: {
  changedReasons?: ChangeReason[];
  assetKey: AssetKeyInput;
}) => {
  if (!changedReasons?.length) {
    return null;
  }
  return (
    <ChangedReasonsPopover changedReasons={changedReasons} assetKey={assetKey}>
      <BaseTag
        fillColor={Colors.backgroundCyan()}
        textColor={Colors.textCyan()}
        label={changedReasons.includes(ChangeReason.NEW) ? 'New in branch' : 'Changed in branch'}
        icon={<Icon name="new_in_branch" color={Colors.accentCyan()} />}
      />
    </ChangedReasonsPopover>
  );
};

export const ChangedReasonsPopover = ({
  changedReasons,
  assetKey,
  children,
}: {
  changedReasons: ChangeReason[];
  assetKey: AssetKeyInput;
  children: React.ReactNode;
}) => {
  const modifiedChanges = changedReasons.filter(
    (reason) => reason !== ChangeReason.NEW && reason !== ChangeReason.REMOVED,
  );
  function getDescription(change: ChangeReason) {
    switch (change) {
      case ChangeReason.NEW:
      case ChangeReason.REMOVED:
        return '';
      case ChangeReason.CODE_VERSION:
        return 'has a changed code version';
      case ChangeReason.DEPENDENCIES:
        return 'has changed dependencies';
      case ChangeReason.PARTITIONS_DEFINITION:
        return 'has a changed partition definition';
      case ChangeReason.TAGS:
        return 'has changed tags';
      case ChangeReason.METADATA:
        return 'has changed metadata';
    }
  }
  return (
    <Popover
      position="top-left"
      isOpen={modifiedChanges.length ? undefined : false}
      usePortal={true}
      content={
        <Box flex={{direction: 'column'}}>
          <Box padding={{horizontal: 12, vertical: 8}} border="bottom">
            <Subtitle2>
              {numberFormatter.format(modifiedChanges.length)}{' '}
              {ifPlural(modifiedChanges.length, 'change', 'changes')} in this branch
            </Subtitle2>
          </Box>
          {modifiedChanges.map((change) => {
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
      {children}
    </Popover>
  );
};

export const MinimalNodeChangedDot = ({
  changedReasons,
  assetKey,
}: {
  changedReasons: ChangeReason[];
  assetKey: AssetKeyInput;
}) => {
  return (
    <ChangedReasonsPopover changedReasons={changedReasons} assetKey={assetKey}>
      <div className={styles.minimalNodeChangedDotContainer} />
    </ChangedReasonsPopover>
  );
};
