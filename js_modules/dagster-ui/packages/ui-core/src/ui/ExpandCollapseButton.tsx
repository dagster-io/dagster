import {Button, Icon, Tooltip} from '@dagster-io/ui-components';

export const ExpandCollapseButton = ({
  expanded,
  onCollapse,
  onExpand,
}: {
  expanded: boolean;
  onCollapse: () => void;
  onExpand: () => void;
}) => (
  <Tooltip content={expanded ? 'Collapse' : 'Expand'}>
    <Button
      icon={<Icon name={expanded ? 'collapse_arrows' : 'expand_arrows'} />}
      onClick={expanded ? onCollapse : onExpand}
    />
  </Tooltip>
);
