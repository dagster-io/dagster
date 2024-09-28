import {Button, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';
import {useLaunchWithTelemetry} from 'shared/launchpad/useLaunchWithTelemetry.oss';

import {
  ExecuteChecksButtonAssetNodeFragment,
  ExecuteChecksButtonCheckFragment,
} from './types/ExecuteChecksButton.types';
import {gql} from '../../apollo-client';
import {CloudOSSContext} from '../../app/CloudOSSContext';
import {usePermissionsForLocation} from '../../app/Permissions';
import {AssetCheckCanExecuteIndividually, ExecutionParams} from '../../graphql/types';

export const ExecuteChecksButton = ({
  assetNode,
  checks,
  label = `Execute all`,
  icon = true,
}: {
  assetNode: ExecuteChecksButtonAssetNodeFragment;
  checks: ExecuteChecksButtonCheckFragment[];
  label?: string;
  icon?: boolean;
}) => {
  const {assetKey, jobNames, repository} = assetNode;
  const [launching, setLaunching] = useState(false);
  const {permissions, disabledReasons} = usePermissionsForLocation(repository.location.name);

  const launchWithTelemetry = useLaunchWithTelemetry();
  const launchable = checks.filter(
    (c) => c.canExecuteIndividually === AssetCheckCanExecuteIndividually.CAN_EXECUTE,
  );

  const iconEl = launching ? (
    <Spinner purpose="caption-text" />
  ) : icon ? (
    <Icon name="execute" />
  ) : null;

  const disabledReason = !permissions.canLaunchPipelineExecution
    ? disabledReasons.canLaunchPipelineExecution
    : checks.length > 0 && launchable.length === 0
    ? 'This check cannot execute without materializing the asset.'
    : checks.length === 0
    ? 'No checks are defined on this asset.'
    : '';

  const {
    featureContext: {canSeeExecuteChecksAction},
  } = useContext(CloudOSSContext);

  if (!canSeeExecuteChecksAction) {
    return null;
  }

  if (disabledReason) {
    return (
      <Tooltip content={disabledReason}>
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
    const executionParams: ExecutionParams = {
      mode: 'default',
      executionMetadata: {},
      runConfigData: '{}',
      selector: {
        jobName,
        repositoryLocationName: repository.location.name,
        repositoryName: repository.name,
        assetSelection: [],
        assetCheckSelection: launchable.map((c) => ({
          assetKey: {path: assetKey.path},
          name: c.name,
        })),
      },
    };
    setLaunching(true);
    await launchWithTelemetry({executionParams}, 'toast');
    setLaunching(false);
  };

  return (
    <Button disabled={launching} icon={iconEl} onClick={onClick}>
      {label}
    </Button>
  );
};

export const EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT = gql`
  fragment ExecuteChecksButtonCheckFragment on AssetCheck {
    name
    canExecuteIndividually
  }
`;

export const EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT = gql`
  fragment ExecuteChecksButtonAssetNodeFragment on AssetNode {
    id
    jobNames
    assetKey {
      path
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
  }
`;
