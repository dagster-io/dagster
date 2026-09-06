import {Box, Colors, Text} from '@dagster-io/ui-components';
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
      <Text
        size={12}
        key="requested"
        style={{
          color: selected
            ? Colors.textBlue()
            : numRequested
              ? Colors.textGreen()
              : Colors.textLight(),
        }}
      >
        {isPartitionedAsset ? `${compactNumber(numRequested)} launched` : 'Launched'}
      </Text>
    ) : null;

  const skipped =
    numSkipped || isPartitionedAsset ? (
      <Text
        size={12}
        key="skipped"
        style={{
          color: selected
            ? Colors.textBlue()
            : numSkipped
              ? Colors.textYellow()
              : Colors.textLight(),
        }}
      >
        {isPartitionedAsset ? `${compactNumber(numSkipped)} skipped` : 'Skipped'}
      </Text>
    ) : null;

  const discarded =
    numDiscarded || isPartitionedAsset ? (
      <Text
        size={12}
        key="discarded"
        style={{
          color: selected
            ? Colors.textBlue()
            : numDiscarded
              ? Colors.textRed()
              : Colors.textLight(),
        }}
      >
        {isPartitionedAsset ? `${compactNumber(numDiscarded)} discarded` : 'Discarded'}
      </Text>
    ) : null;

  const filtered = [requested, skipped, discarded].filter(
    (element): element is React.ReactElement => !!element,
  );

  return (
    <Box flex={{direction: 'row', gap: 2, alignItems: 'center'}} style={{whiteSpace: 'nowrap'}}>
      {filtered
        .map((element, ii) => [
          element,
          <Text key={`spacer-${ii}`} size={12} color={selected ? 'textBlue' : 'textLighter'}>
            /
          </Text>,
        ])
        .flat()
        .slice(0, -1)}
    </Box>
  );
});
