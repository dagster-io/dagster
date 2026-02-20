import {PageHeader, Subtitle1} from '@dagster-io/ui-components';

import {useFullScreen} from '../../app/AppTopNav/AppTopNavContext';
import {ReloadAllButton} from '../../workspace/ReloadAllButton';

export const AssetsGraphHeader = () => {
  const {isFullScreen} = useFullScreen();
  if (isFullScreen) {
    return null;
  }
  return (
    <PageHeader
      title={<Subtitle1>Global Asset Lineage</Subtitle1>}
      right={<ReloadAllButton label="Reload definitions" />}
    />
  );
};
