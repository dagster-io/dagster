import {Box, Icon, IconWrapper} from '@dagster-io/ui-components';
import styled from 'styled-components';

const INTEGRATIONS_ORIGIN_AND_PATH = 'https://integration-registry.dagster.io/logos';

interface Props {
  name: string;
  logoFilename: string | null;
}

export const IntegrationIcon = ({name, logoFilename}: Props) => {
  const icon = () => {
    if (logoFilename === null) {
      return <Icon name="workspace" size={24} />;
    }

    return (
      <IntegrationIconWrapper
        role="img"
        $size={32}
        $img={`${INTEGRATIONS_ORIGIN_AND_PATH}/${logoFilename}`}
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

const IntegrationIconWrapper = styled(IconWrapper)`
  mask-size: contain;
  mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-position: center;
`;
