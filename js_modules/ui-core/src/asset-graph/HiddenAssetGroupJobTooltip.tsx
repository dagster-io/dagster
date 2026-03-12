import {Colors, Icon, Tooltip} from '@dagster-io/ui-components';

import {HIDDEN_ASSET_GROUP_JOB_TOOLTIP} from './Utils';

export const HiddenAssetGroupJobTooltipIcon = ({size = 12}: {size?: 12 | 16}) => (
  <Tooltip
    content={<div style={{maxWidth: '300px'}}>{HIDDEN_ASSET_GROUP_JOB_TOOLTIP}</div>}
    placement="top"
  >
    <Icon name="info" color={Colors.accentGray()} size={size} />
  </Tooltip>
);
