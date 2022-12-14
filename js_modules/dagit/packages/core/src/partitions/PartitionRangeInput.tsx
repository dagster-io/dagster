import {Icon, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {ClearButton} from '../ui/ClearButton';

import {partitionsToText, textToPartitions} from './SpanRepresentation';

export const PartitionRangeInput: React.FC<{
  value: string[];
  onChange: (partitionNames: string[]) => void;
  partitionKeys: string[];
  isTimeseries: boolean;
}> = ({value, onChange, partitionKeys, isTimeseries}) => {
  const [valueString, setValueString] = React.useState('');
  const partitionNameJSON = React.useMemo(() => JSON.stringify(partitionKeys), [partitionKeys]);

  React.useEffect(() => {
    const partitionNameArr = JSON.parse(partitionNameJSON);
    setValueString(isTimeseries ? partitionsToText(value, partitionNameArr) : value.join(', '));
  }, [value, partitionNameJSON, isTimeseries]);

  const placeholder = React.useMemo(() => {
    return placeholderForPartitions(partitionKeys, isTimeseries);
  }, [partitionKeys, isTimeseries]);

  const tryCommit = (e: React.SyntheticEvent<HTMLInputElement>) => {
    try {
      onChange(textToPartitions(valueString, partitionKeys));
    } catch (err: any) {
      e.preventDefault();
      showCustomAlert({body: err.message});
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      tryCommit(e);
    }
  };

  return (
    <TextInput
      placeholder={placeholder}
      value={valueString}
      style={{display: 'flex', width: '100%', flex: 1, flexGrow: 1}}
      onChange={(e) => setValueString(e.currentTarget.value)}
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
export function placeholderForPartitions(names: string[], isTimeseries: boolean) {
  if (names.length === 0) {
    return '';
  }
  if (names.length < 4 || !isTimeseries) {
    return `ex: ${names[0]}, ${names[1]}`;
  }
  return `ex: ${names[0]}, ${names[1]}, [${names[2]}...${names[names.length - 1]}]`;
}
