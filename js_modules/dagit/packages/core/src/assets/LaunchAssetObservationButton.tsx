import {Button, Spinner, Tooltip, Icon} from '@dagster-io/ui';
import React from 'react';

import {AssetsInScope, useAssetLaunchAction} from './LaunchAssetExecutionButton';

export const LaunchAssetObservationButton: React.FC<{
  scope: AssetsInScope;
  intent?: 'primary' | 'none';
  preferredJobName?: string;
}> = ({scope, preferredJobName, intent = 'none'}) => {
  const {onClick, launchpadElement, loading} = useAssetLaunchAction({
    preferredJobName,
    type: 'observation',
  });

  const scopeAssets = 'selected' in scope ? scope.selected : scope.all;
  if (!scopeAssets.length) {
    return <span />;
  }

  const count = scopeAssets.length > 1 ? ` (${scopeAssets.length})` : '';
  const label =
    'selected' in scope
      ? `Observe selected${count}`
      : scope.skipAllTerm
      ? `Observe${count}`
      : `Observe sources ${count}`;

  const hasMaterializePermission = scopeAssets.every((a) => a.hasMaterializePermission);
  if (!hasMaterializePermission) {
    return (
      <Tooltip content="You do not have permission to observe source assets">
        <Button intent={intent} icon={<Icon name="observation" />} disabled>
          {label}
        </Button>
      </Tooltip>
    );
  }

  return (
    <>
      <Button
        intent={intent}
        onClick={(e) =>
          onClick(
            scopeAssets.map((a) => a.assetKey),
            e,
          )
        }
        icon={loading ? <Spinner purpose="body-text" /> : <Icon name="observation" />}
      >
        {label}
      </Button>
      {launchpadElement}
    </>
  );
};
