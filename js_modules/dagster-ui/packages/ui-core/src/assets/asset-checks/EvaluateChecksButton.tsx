import {Button, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import React, {useState} from 'react';

import {usePermissionsForLocation} from '../../app/Permissions';
import {AssetKeyInput} from '../../graphql/types';
import {useLaunchPadHooks} from '../../launchpad/LaunchpadHooksContext';

export type EvaluateChecksAssetNode = {
  assetKey: AssetKeyInput;
  repository: {name: string; location: {name: string}};
  jobNames: string[];
};

export const EvaluateChecksButton = ({
  assetNode,
  checks,
  label = `Evaluate all`,
  icon = true,
}: {
  assetNode: EvaluateChecksAssetNode;
  checks: {name: string}[];
  label?: string;
  icon?: boolean;
}) => {
  const {assetKey, jobNames, repository} = assetNode;
  const [launching, setLaunching] = useState(false);
  const {permissions, disabledReasons} = usePermissionsForLocation(repository.location.name);

  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();

  const iconEl = launching ? (
    <Spinner purpose="caption-text" />
  ) : icon ? (
    <Icon name="execute" />
  ) : null;

  if (!permissions.canLaunchPipelineExecution) {
    return (
      <Tooltip content={disabledReasons.canLaunchPipelineExecution}>
        <Button icon={iconEl} disabled>
          {label}
        </Button>
      </Tooltip>
    );
  }

  const jobName = jobNames[0];
  if (!jobName) {
    return (
      <Tooltip content="No jobs were found to execute the selected checks">
        <Button icon={iconEl} disabled>
          {label}
        </Button>
      </Tooltip>
    );
  }

  const onClick = async () => {
    const params = {
      executionParams: {
        mode: 'default',
        executionMetadata: {},
        runConfigData: '{}',
        selector: {
          repositoryLocationName: repository.location.name,
          repositoryName: repository.name,
          jobName,
          assetCheckSelection: checks.map((c) => ({
            assetKey: {path: assetKey.path},
            name: c.name,
          })),
        },
      },
    };
    setLaunching(true);
    await launchWithTelemetry(params, 'toast');
    setLaunching(false);
  };

  return (
    <Button disabled={launching} icon={iconEl} onClick={onClick}>
      {label}
    </Button>
  );
};
