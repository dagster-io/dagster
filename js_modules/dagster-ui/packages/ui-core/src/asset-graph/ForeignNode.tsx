import {Colors, Icon} from '@dagster-io/ui-components';
import {memo} from 'react';

import {ASSET_LINK_NAME_MAX_LENGTH} from './layout';
import {withMiddleTruncation} from '../app/Util';
import styles from './css/ForeignNode.module.css';

export const AssetNodeLink = memo(({assetKey}: {assetKey: {path: string[]}}) => {
  const label = assetKey.path[assetKey.path.length - 1]!;
  return (
    <div className={styles.assetNodeLinkContainer}>
      <Icon name="open_in_new" color={Colors.linkDefault()} />
      <span className="label" title={label}>
        {withMiddleTruncation(label, {
          maxLength: ASSET_LINK_NAME_MAX_LENGTH,
        })}
      </span>
    </div>
  );
});
