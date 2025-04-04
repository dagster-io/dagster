import {Box, Icon, IconWrapper} from '@dagster-io/ui-components';
import styled from 'styled-components';

interface Props {
  name: string;
  logo: string | {src: string} | null;
}

export const IntegrationIcon = ({name, logo}: Props) => {
  const icon = () => {
    if (logo === null) {
      return <Icon name="workspace" size={24} />;
    }

    return (
      <IntegrationIconWrapper
        role="img"
        $size={32}
        $img={extractIconSrc(logo)}
        $color={null}
        $rotation={null}
        aria-label={name}
      />
    );
  };

  return (
    <Box
      flex={{alignItems: 'center', justifyContent: 'center'}}
      border="all"
      style={{borderRadius: 8, height: 48, width: 48}}
      padding={8}
    >
      {icon()}
    </Box>
  );
};

function extractIconSrc(iconSvg: string | {src: string}) {
  // Storybook imports SVGs are string but nextjs imports them as object.
  // This is a temporary work around until we can get storybook to import them the same way as nextjs
  if (typeof iconSvg !== 'undefined') {
    return typeof iconSvg === 'string' ? (iconSvg as any) : iconSvg?.src;
  }
  return '';
}

const IntegrationIconWrapper = styled(IconWrapper)`
  mask-size: contain;
  mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-position: center;
`;
