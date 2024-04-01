// eslint-disable-next-line no-restricted-imports
import {Colors, Icon, IconName, IconNames, IconWrapper} from '@dagster-io/ui-components';

import {KNOWN_TAGS} from '../graph/OpTags';

type IntegrationIconName = keyof typeof KNOWN_TAGS;
export type InsightsIconType = IconName | IntegrationIconName;

interface InsightsIconProps {
  name: InsightsIconType;
  color?: string;
}

export const InsightsIcon = (props: InsightsIconProps) => {
  const {name, color = Colors.accentPrimary()} = props;
  if (IconNames.includes(name as IconName)) {
    return <Icon name={name as IconName} style={{marginLeft: 0}} color={color} />;
  } else {
    const known = KNOWN_TAGS[props.name as IntegrationIconName];
    const src = 'icon' in known ? known.icon.src : '';
    return (
      <IconWrapper
        role="img"
        $size={16}
        $img={src}
        $color={color}
        $rotation={null}
        style={{marginLeft: 0}}
        aria-label={props.name}
      />
    );
  }
};
