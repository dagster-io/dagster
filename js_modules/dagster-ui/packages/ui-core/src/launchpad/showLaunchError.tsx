import {FontFamily} from '@dagster-io/ui-components';

import {showCustomAlert} from '../app/CustomAlertProvider';

export const showLaunchError = (error: Error) => {
  console.error('Error launching run:', error);

  const body =
    error.message === 'Failed to fetch' ? (
      <div style={{fontFamily: FontFamily.default}}>
        请确保 Dagster 网页服务器正在运行，然后重试。
      </div>
    ) : (
      <div>{error.message}</div>
    );

  showCustomAlert({
    title: '无法启动运行',
    body,
  });
};
