import {Alert, Colors, Icon} from '@dagster-io/ui-components';

export const AssetChecksBanner = ({onClose}: {onClose: () => void}) => {
  return (
    <Alert
      intent="info"
      title="Asset Checks are experimental"
      icon={<Icon name="info" color={Colors.accentBlue()} />}
      onClose={onClose}
    />
  );
};
