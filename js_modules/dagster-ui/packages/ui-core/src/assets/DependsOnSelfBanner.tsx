import {Alert, Colors, Icon} from '@dagster-io/ui-components';

export const DependsOnSelfBanner = () => {
  return (
    <Alert
      intent="info"
      icon={
        <Icon
          name="history_toggle_off"
          size={16}
          color={Colors.accentBlue()}
          style={{marginTop: 1}}
        />
      }
      title={
        <div style={{fontWeight: 400}}>This asset depends on earlier partitions of itself. </div>
      }
    />
  );
};
