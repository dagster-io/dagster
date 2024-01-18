import * as React from 'react';

import {Box, Spinner, Tooltip, useDelayedState} from '@dagster-io/ui-components';

interface Props {
  tooltipContent: string | React.ReactElement | null;
}

const SPINNER_WAIT_MSEC = 2000;

export const SearchInputSpinner = (props: Props) => {
  const {tooltipContent} = props;
  const canShowSpinner = useDelayedState(SPINNER_WAIT_MSEC);

  if (!canShowSpinner) {
    return null;
  }

  return (
    <Box margin={{top: 1}}>
      <Tooltip placement="top" canShow={!!tooltipContent} content={tooltipContent || ''}>
        <Spinner purpose="body-text" />
      </Tooltip>
    </Box>
  );
};
