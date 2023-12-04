import {
  Box,
  Caption,
  colorTextBlue,
  colorTextGreen,
  colorTextLight,
  colorTextLighter,
  colorTextRed,
  colorTextYellow,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {compactNumber} from '../../ui/formatters';

interface Props {
  numRequested: number;
  numSkipped: number;
  numDiscarded: number;
  isPartitionedAsset: boolean;
  selected: boolean;
}

export const EvaluationCounts = React.memo((props: Props) => {
  const {numRequested, numSkipped, numDiscarded, isPartitionedAsset, selected} = props;

  const requested =
    numRequested || isPartitionedAsset ? (
      <Caption
        key="requested"
        color={selected ? colorTextBlue() : numRequested ? colorTextGreen() : colorTextLight()}
      >
        {isPartitionedAsset ? `${compactNumber(numRequested)} launched` : 'Launched'}
      </Caption>
    ) : null;

  const skipped =
    numSkipped || isPartitionedAsset ? (
      <Caption
        key="skipped"
        color={selected ? colorTextBlue() : numSkipped ? colorTextYellow() : colorTextLight()}
      >
        {isPartitionedAsset ? `${compactNumber(numSkipped)} skipped` : 'Skipped'}
      </Caption>
    ) : null;

  const discarded =
    numDiscarded || isPartitionedAsset ? (
      <Caption
        key="discarded"
        color={selected ? colorTextBlue() : numDiscarded ? colorTextRed() : colorTextLight()}
      >
        {isPartitionedAsset ? `${compactNumber(numDiscarded)} discarded` : 'Discarded'}
      </Caption>
    ) : null;

  const filtered = [requested, skipped, discarded].filter(
    (element): element is React.ReactElement => !!element,
  );

  return (
    <Box flex={{direction: 'row', gap: 2, alignItems: 'center'}} style={{whiteSpace: 'nowrap'}}>
      {filtered
        .map((element, ii) => [
          element,
          <Caption key={`spacer-${ii}`} color={selected ? colorTextBlue() : colorTextLighter()}>
            /
          </Caption>,
        ])
        .flat()
        .slice(0, -1)}
    </Box>
  );
});
