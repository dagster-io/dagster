import {
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  TextArea,
  showToast,
} from '@dagster-io/ui-components';
import {useState} from 'react';

import 'chartjs-adapter-date-fns';

import {gql, useMutation} from '../apollo-client';
import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from './types/EditCursorDialog.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {showMutationErrorToast} from '../app/showMutationErrorToast';
import {SensorSelector} from '../graphql/types';

export const EditCursorDialog = ({
  isOpen,
  sensorSelector,
  cursor,
  onClose,
}: {
  isOpen: boolean;
  cursor: string;
  sensorSelector: SensorSelector;
  onClose: () => void;
}) => {
  const [cursorValue, setCursorValue] = useState(cursor);
  const [requestSet, {loading: isSaving}] = useMutation<
    SetSensorCursorMutation,
    SetSensorCursorMutationVariables
  >(SET_CURSOR_MUTATION);

  const onSave = async () => {
    const {data} = await requestSet({
      variables: {sensorSelector, cursor: cursorValue},
    });
    if (!showMutationErrorToast(data?.setSensorCursor, 'Sensor', 'Could not set cursor value.')) {
      showToast({message: 'Cursor value updated', intent: 'success'});
    }
    onClose();
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={() => {
        onClose();
        setCursorValue(cursor);
      }}
      style={{
        width: '500px',
      }}
      title={`Edit ${sensorSelector.sensorName} cursor`}
    >
      <DialogBody>
        <TextArea
          value={cursorValue}
          resize="vertical"
          onChange={(e) => setCursorValue(e.target.value)}
          style={{width: '100%'}}
        />
      </DialogBody>
      <DialogFooter>
        <Button onClick={onClose}>Cancel</Button>
        <Button intent="primary" onClick={onSave} disabled={isSaving}>
          Set cursor value
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

export const SET_CURSOR_MUTATION = gql`
  mutation SetSensorCursorMutation($sensorSelector: SensorSelector!, $cursor: String) {
    setSensorCursor(sensorSelector: $sensorSelector, cursor: $cursor) {
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
      ... on SensorNotFoundError {
        message
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
