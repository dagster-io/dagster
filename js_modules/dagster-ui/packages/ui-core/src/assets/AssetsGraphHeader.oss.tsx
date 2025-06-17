import {PageHeader, Subtitle1} from '@dagster-io/ui-components';

import {ReloadAllButton} from '../workspace/ReloadAllButton';

export const AssetsGraphHeader = () => {
  return (
    <PageHeader
      title={<Subtitle1>Global Asset Lineage</Subtitle1>}
      right={<ReloadAllButton label="Reload definitions" />}
    />
  );
};
