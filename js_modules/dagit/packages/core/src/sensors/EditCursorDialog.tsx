import {gql, useMutation} from '@apollo/client';
import {TextArea} from '@blueprintjs/core';
import {ButtonWIP, DialogBody, DialogFooter, DialogWIP} from '@dagster-io/ui';
import * as React from 'react';

import 'chartjs-adapter-date-fns';

import {SharedToaster} from '../app/DomUtils';
import {SensorSelector} from '../types/globalTypes';

export const EditCursorDialog: React.FC<{
  cursor: string;
  sensorSelector: SensorSelector;
  onClose: () => void;
}> = ({sensorSelector, cursor, onClose}) => {
  const [cursorValue, setCursorValue] = React.useState(cursor);
  const [isSaving, setIsSaving] = React.useState(false);
  const [requestSet] = useMutation(SET_CURSOR_MUTATION);

  const onSave = async () => {
    setIsSaving(true);
    const {data} = await requestSet({
      variables: {sensorSelector, cursor: cursorValue},
    });
    if (data?.setSensorCursor.__typename === 'Sensor') {
      SharedToaster.show({message: 'Set cursor value', intent: 'success'});
    } else {
      SharedToaster.show({message: 'Could not set cursor value', intent: 'danger'});
    }
    onClose();
  };

  return (
    <DialogWIP
      isOpen={true}
      onClose={onClose}
      style={{
        width: '50vw',
      }}
      title={`Edit ${sensorSelector.sensorName} cursor`}
    >
      <DialogBody>
        <TextArea
          value={cursorValue}
          onChange={(e) => setCursorValue(e.target.value)}
          style={{width: '100%'}}
        />
      </DialogBody>
      <DialogFooter>
        <ButtonWIP onClick={onClose}>Cancel</ButtonWIP>
        <ButtonWIP intent="primary" onClick={onSave} disabled={isSaving}>
          Set cursor value
        </ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

const SET_CURSOR_MUTATION = gql`
  mutation SetSensorCursorMutation($sensorSelector: SensorSelector!, $cursor: String) {
    setSensorCursor(sensorSelector: $sensorSelector, cursor: $cursor) {
      ... on PythonError {
        message
        className
        stack
      }
      ... on Sensor {
        id
        sensorState {
          id
          status
          typeSpecificData {
            ... on SensorData {
              lastCursor
            }
          }
        }
      }
    }
  }
`;
