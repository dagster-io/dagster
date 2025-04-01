// eslint-disable-next-line no-restricted-imports
import {Colors, Icon, IconName, IconNames, IconWrapper} from '@dagster-io/ui-components';

import {KNOWN_TAGS, KnownTagType, extractIconSrc} from '../graph/OpTags';

type IntegrationIconName = KnownTagType;
export type InsightsIconType = IconName | IntegrationIconName;

interface InsightsIconProps {
  name: InsightsIconType;
  color?: string;
  size?: number;
}

export const InsightsIcon = (props: InsightsIconProps) => {
  const {name, color = Colors.accentPrimary(), size = 16} = props;
  if (IconNames.includes(name as IconName)) {
    return <Icon name={name as IconName} style={{marginLeft: 0}} color={color} />;
  } else {
    const known = KNOWN_TAGS[props.name as IntegrationIconName];
    return (
      <IconWrapper
        role="img"
        $size={size}
        $img={extractIconSrc(known)}
        $color={color}
        $rotation={null}
        style={{marginLeft: 0}}
        aria-label={props.name}
      />
    );
  }
};
