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
        color={selected ? Colors.Blue700 : numRequested ? Colors.Green700 : Colors.Gray700}
      >
        {isPartitionedAsset ? `${compactNumber(numRequested)} launched` : 'Launched'}
      </Caption>
    ) : null;

  const skipped =
    numSkipped || isPartitionedAsset ? (
      <Caption
        key="skipped"
        color={selected ? Colors.Blue700 : numSkipped ? Colors.Yellow700 : Colors.Gray700}
      >
        {isPartitionedAsset ? `${compactNumber(numSkipped)} skipped` : 'Skipped'}
      </Caption>
    ) : null;

  const discarded =
    numDiscarded || isPartitionedAsset ? (
      <Caption
        key="discarded"
        color={selected ? Colors.Blue700 : numDiscarded ? Colors.Red700 : Colors.Gray700}
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
          <Caption key={`spacer-${ii}`} color={selected ? Colors.Blue200 : Colors.Gray200}>
            /
          </Caption>,
        ])
        .flat()
        .slice(0, -1)}
    </Box>
  );
});
