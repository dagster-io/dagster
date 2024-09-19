import {Icon, TextInput} from '@dagster-io/ui-components';
import * as React from 'react';

import {partitionsToText, spanTextToSelectionsOrError} from './SpanRepresentation';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {testId} from '../testing/testId';
import {ClearButton} from '../ui/ClearButton';

export const DimensionRangeInput = ({
  value,
  onChange,
  partitionKeys,
  isTimeseries,
}: {
  value: string[];
  onChange: (partitionNames: string[]) => void;
  partitionKeys: string[];
  isTimeseries: boolean;
}) => {
  const [valueString, setValueString] = React.useState('');

  const valueJSON = React.useMemo(() => JSON.stringify(value), [value]);
  const partitionNameJSON = React.useMemo(() => JSON.stringify(partitionKeys), [partitionKeys]);

  React.useEffect(() => {
    // Only reset the valueString if the valueJSON meaningfully changes
    const partitionNameArr = JSON.parse(partitionNameJSON);
    const valueArr = JSON.parse(valueJSON);
    setValueString(
      isTimeseries ? partitionsToText(valueArr, partitionNameArr) : valueArr.join(', '),
    );
  }, [valueJSON, partitionNameJSON, isTimeseries]);

  const placeholder = React.useMemo(() => {
    return partitionKeys.length === 0
      ? 'Loading partition keys...'
      : placeholderForPartitions(partitionKeys, isTimeseries);
  }, [partitionKeys, isTimeseries]);

  const tryCommit = (e: React.SyntheticEvent<HTMLInputElement>) => {
    const selections = spanTextToSelectionsOrError(partitionKeys, valueString);
    if (selections instanceof Error) {
      e.preventDefault();
      showCustomAlert({body: selections.message});
    } else {
      onChange(selections.selectedKeys);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      tryCommit(e);
    }
  };

  return (
    <TextInput
      data-testid={testId('dimension-range-input')}
      placeholder={placeholder}
      value={valueString}
      style={{display: 'flex', width: '100%', flex: 1, flexGrow: 1}}
      onChange={(e) => {
        setValueString(e.currentTarget.value);
      }}
      onKeyDown={onKeyDown}
      onBlur={tryCommit}
      rightElement={
        <ClearButton
          style={{display: valueString.length ? 'initial' : 'none'}}
          onClick={() => onChange([])}
        >
          <Icon name="cancel" />
        </ClearButton>
      }
    />
  );
};

function placeholderForPartitions(names: string[], isTimeseries: boolean) {
  if (names.length === 0) {
    return '';
  }
  if (names.length < 4 || !isTimeseries) {
    return `ex: ${names[0]}, ${names[1]}`;
  }
  return `ex: ${names[0]}, ${names[1]}, [${names[2]}...${names[names.length - 1]}]`;
}
