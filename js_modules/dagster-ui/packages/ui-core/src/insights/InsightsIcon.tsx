import {BaseIcon, Colors, Icon, IconName, IconNames, IconSize} from '@dagster-io/ui-components';

import {KNOWN_TAGS, KnownTagType, extractIconSrc} from '../graph/OpTags';

type IntegrationIconName = KnownTagType;
export type InsightsIconType = IconName | IntegrationIconName;

interface InsightsIconProps {
  name: InsightsIconType;
  color?: string;
  size?: IconSize;
}

export const InsightsIcon = (props: InsightsIconProps) => {
  const {name, ...rest} = props;
  if (IconNames.includes(name as IconName)) {
    return <Icon {...rest} name={name as IconName} />;
  }

  const known = KNOWN_TAGS[props.name as IntegrationIconName];
  return (
    <BaseIcon
      {...rest}
      img={extractIconSrc(known)}
      name={name}
      style={{backgroundColor: 'transparent'}}
    />
  );
};
