import {gql, useMutation} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {TextArea} from '@blueprintjs/core';
import {ButtonLink, Button, Colors, DialogBody, DialogFooter, Dialog, Group} from '@dagster-io/ui';
import * as React from 'react';

import 'chartjs-adapter-date-fns';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {SensorSelector} from '../types/globalTypes';

import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from './types/SetSensorCursorMutation';

export const EditCursorDialog: React.FC<{
  cursor: string;
  sensorSelector: SensorSelector;
  onClose: () => void;
}> = ({sensorSelector, cursor, onClose}) => {
  const [cursorValue, setCursorValue] = React.useState(cursor);
  const [isSaving, setIsSaving] = React.useState(false);
  const [requestSet] = useMutation<SetSensorCursorMutation, SetSensorCursorMutationVariables>(
    SET_CURSOR_MUTATION,
  );

  const onSave = async () => {
    setIsSaving(true);
    const {data} = await requestSet({
      variables: {sensorSelector, cursor: cursorValue},
    });
    if (data?.setSensorCursor.__typename === 'Sensor') {
      SharedToaster.show({message: 'Cursor value updated', intent: 'success'});
    } else if (data?.setSensorCursor) {
      const error = data.setSensorCursor;
      SharedToaster.show({
        intent: 'danger',
        message: (
          <Group direction="row" spacing={8}>
            <div>Could not set cursor value.</div>
            <ButtonLink
              color={Colors.White}
              underline="always"
              onClick={() => {
                showCustomAlert({
                  title: 'Python Error',
                  body:
                    error.__typename === 'PythonError' ? (
                      <PythonErrorInfo error={error} />
                    ) : (
                      'Sensor not found'
                    ),
                });
              }}
            >
              View error
            </ButtonLink>
          </Group>
        ),
      });
    }
    onClose();
  };

  return (
    <Dialog
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
        <Button onClick={onClose}>Cancel</Button>
        <Button intent="primary" onClick={onSave} disabled={isSaving}>
          Set cursor value
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const SET_CURSOR_MUTATION = gql`
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
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
