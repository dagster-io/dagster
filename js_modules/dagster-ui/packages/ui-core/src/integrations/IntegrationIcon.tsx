import {Box, IconWrapper} from '@dagster-io/ui-components';
import {Spacing} from '@dagster-io/ui-components/src/components/types';
import styled from 'styled-components';

import {KNOWN_TAGS, KnownTagType, extractIconSrc} from '../graph/OpTags';

interface Props {
  name: string;
  knownTag: KnownTagType;
  padding?: Spacing;
}

export const IntegrationIcon = ({name, knownTag, padding = 8}: Props) => {
  return (
    <Box padding={padding} border="all" style={{borderRadius: 8}}>
      <IntegrationIconWrapper
        role="img"
        $size={32}
        $img={extractIconSrc(KNOWN_TAGS[knownTag])}
        $color={null}
        $rotation={null}
        aria-label={name}
      />
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
