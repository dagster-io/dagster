import {Box, Caption, Colors} from '@dagster-io/ui-components';
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
        color={
          selected ? Colors.textBlue() : numRequested ? Colors.textGreen() : Colors.textLight()
        }
      >
        {isPartitionedAsset ? `${compactNumber(numRequested)} launched` : 'Launched'}
      </Caption>
    ) : null;

  const skipped =
    numSkipped || isPartitionedAsset ? (
      <Caption
        key="skipped"
        color={selected ? Colors.textBlue() : numSkipped ? Colors.textYellow() : Colors.textLight()}
      >
        {isPartitionedAsset ? `${compactNumber(numSkipped)} skipped` : 'Skipped'}
      </Caption>
    ) : null;

  const discarded =
    numDiscarded || isPartitionedAsset ? (
      <Caption
        key="discarded"
        color={selected ? Colors.textBlue() : numDiscarded ? Colors.textRed() : Colors.textLight()}
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
          <Caption key={`spacer-${ii}`} color={selected ? Colors.textBlue() : Colors.textLighter()}>
            /
          </Caption>,
        ])
        .flat()
        .slice(0, -1)}
    </Box>
  );
});
