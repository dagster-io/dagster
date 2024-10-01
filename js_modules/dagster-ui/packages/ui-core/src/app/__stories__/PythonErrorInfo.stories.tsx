// eslint-disable-next-line no-restricted-imports
import {Meta} from '@storybook/react';

import {buildErrorChainLink, buildPythonError} from '../../graphql/types';
import {PythonErrorInfo} from '../PythonErrorInfo';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'PythonErrorInfo',
} as Meta;

const error = buildPythonError({
  message:
    'dagster._core.errors.SensorExecutionError: Error occurred during the execution of evaluation_fn for sensor toy_file_sensor\n',
  stack: [
    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_grpc/impl.py", line 328, in get_external_sensor_execution\n    return sensor_def.evaluate_tick(sensor_context)\n',
    '  File "/Users/marcosalazar/.pyenv/versions/3.9.9/lib/python3.9/contextlib.py", line 137, in __exit__\n    self.gen.throw(typ, value, traceback)\n',
    '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/errors.py", line 213, in user_code_error_boundary\n    raise error_cls(\n',
  ],
  errorChain: [
    buildErrorChainLink({
      isExplicitLink: true,
      error: buildPythonError({
        message: 'Exception: testing\n',
        stack: [
          '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/errors.py", line 206, in user_code_error_boundary\n    yield\n',
          '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_grpc/impl.py", line 328, in get_external_sensor_execution\n    return sensor_def.evaluate_tick(sensor_context)\n',
          '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/sensor_definition.py", line 428, in evaluate_tick\n    result = list(self._evaluation_fn(context))\n',
          '  File "/Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/sensor_definition.py", line 598, in _wrapped_fn\n    for item in result:\n',
          '  File "/Users/marcosalazar/code/dagster/python_modules/dagster-test/dagster_test/toys/sensors.py", line 76, in toy_file_sensor\n',
        ],
      }),
    }),
  ],
});

export const Error = () => {
  return <PythonErrorInfo error={error} />;
};
