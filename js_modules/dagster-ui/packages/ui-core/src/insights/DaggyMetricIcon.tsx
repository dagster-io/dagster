import {IconWrapper} from '@dagster-io/ui-components';
import {memo} from 'react';
import styled from 'styled-components';

import daggy from './svg/daggy.svg';

export const DaggyMetricIcon = memo(() => {
  return (
    <DaggyWrapper
      role="img"
      aria-label="Dagster metric"
      $color={null}
      $rotation={null}
      $size={16}
      $img={daggy.src}
    />
  );
});

const DaggyWrapper = styled(IconWrapper)`
  mask-size: contain;
  mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-size: contain;
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-position: center;
`;
