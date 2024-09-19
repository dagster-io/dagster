import {
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  TextArea,
} from '@dagster-io/ui-components';
import {useState} from 'react';

import 'chartjs-adapter-date-fns';

import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from './types/EditCursorDialog.types';
import {gql, useMutation} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
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
    if (data?.setSensorCursor.__typename === 'Sensor') {
      await showSharedToaster({message: 'Cursor value updated', intent: 'success'});
    } else if (data?.setSensorCursor) {
      const error = data.setSensorCursor;
      await showSharedToaster({
        intent: 'danger',
        message: (
          <Group direction="row" spacing={8}>
            <div>Could not set cursor value.</div>
            <ButtonLink
              color={Colors.accentReversed()}
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
          $resize="vertical"
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
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
