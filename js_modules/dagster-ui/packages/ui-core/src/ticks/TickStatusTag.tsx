import {
  Tag,
  Dialog,
  DialogBody,
  DialogFooter,
  Button,
  BaseTag,
  Colors,
  Box,
  ButtonLink,
} from '@dagster-io/ui-components';
import React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {InstigationTickStatus} from '../graphql/types';

export const TickStatusTag = ({
  count,
  error,
  status,
}: {
  status: InstigationTickStatus;
  count: number;
  error?: PythonErrorFragment | null;
}) => {
  const [showErrors, setShowErrors] = React.useState(false);
  const tag = React.useMemo(() => {
    switch (status) {
      case InstigationTickStatus.STARTED:
        return (
          <Tag intent="primary" icon="spinner">
            Evaluating
          </Tag>
        );
      case InstigationTickStatus.SKIPPED:
        return <BaseTag fillColor={Colors.Olive50} label="0 requested" />;
      case InstigationTickStatus.FAILURE:
        return (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
            <Tag intent="danger">Failure</Tag>
            {error ? (
              <ButtonLink
                onClick={() => {
                  setShowErrors(true);
                }}
              >
                View
              </ButtonLink>
            ) : null}
          </Box>
        );
      case InstigationTickStatus.SUCCESS:
        return <Tag intent="success">{count} requested</Tag>;
    }
  }, [error, count, status]);

  return (
    <>
      {tag}
      {error ? (
        <Dialog isOpen={showErrors} title="Error" style={{width: '80vw'}}>
          <DialogBody>
            <PythonErrorInfo error={error} />
          </DialogBody>
          <DialogFooter topBorder>
            <Button
              intent="primary"
              onClick={() => {
                setShowErrors(false);
              }}
            >
              Close
            </Button>
          </DialogFooter>
        </Dialog>
      ) : null}
    </>
  );
};
