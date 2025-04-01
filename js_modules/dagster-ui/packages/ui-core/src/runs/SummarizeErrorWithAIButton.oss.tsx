import {Button} from '@dagster-io/ui-components';

import {GenericError} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';

export const SummarizeErrorWithAIButton = (
  _: {
    error: PythonErrorFragment | GenericError;
  } & React.ComponentProps<typeof Button>,
) => {
  return null;
};
