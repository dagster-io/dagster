import {
  Box,
  Button,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import {useLaunchWithTelemetry} from '@shared/launchpad/useLaunchWithTelemetry';
import {useContext, useState} from 'react';

import styles from './css/ExecuteChecksButton.module.css';
import {
  ExecuteChecksButtonAssetNodeFragment,
  ExecuteChecksButtonCheckFragment,
} from './types/ExecuteChecksButton.types';
import {gql} from '../../apollo-client';
import {CloudOSSContext} from '../../app/CloudOSSContext';
import {usePermissionsForLocation} from '../../app/Permissions';
import {AssetCheckCanExecuteIndividually, ExecutionParams} from '../../graphql/types';

type DropdownOption = {
  label: string;
  icon: string;
  onClick: () => void;
  disabled?: boolean;
  disabledReason?: string;
};

type ExecuteChecksButtonProps = {
  assetNode: ExecuteChecksButtonAssetNodeFragment;
  checks: ExecuteChecksButtonCheckFragment[];
  label?: string;
  icon?: boolean;
  isPartitioned?: boolean;
  additionalDropdownOptions?: DropdownOption[];
};

export const ExecuteChecksButton = ({
  assetNode,
  checks,
  label = `Execute all`,
  icon = true,
  isPartitioned = false,
  additionalDropdownOptions,
}: ExecuteChecksButtonProps) => {
  const {assetKey, jobNames: assetJobNames, repository} = assetNode;
  const [launching, setLaunching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
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

  const {
    featureContext: {canSeeExecuteChecksAction},
  } = useContext(CloudOSSContext);

  if (!canSeeExecuteChecksAction) {
    return null;
  }

  const commonCheckJobNames = checks.reduce((commonJobNames, check) => {
    return commonJobNames.filter((name: string) => check.jobNames.includes(name));
  }, checks[0]?.jobNames || []);

  // Ideally all the checks have a common job name, but sub 1.5.10 user code versions
  // do not report job names for checks so fallback to the original behavior that was
  // here of using the first job name of the asset.
  const resolvedJobName =
    commonCheckJobNames.length > 0 ? commonCheckJobNames[0] : assetJobNames[0];

  const mainActionDisabledReason = (() => {
    if (!permissions.canLaunchPipelineExecution) {
      return disabledReasons.canLaunchPipelineExecution;
    }
    if (checks.length > 0 && launchable.length === 0) {
      return 'This check cannot execute without materializing the asset.';
    }
    if (checks.length === 0) {
      return 'No checks are defined on this asset.';
    }
    if (!resolvedJobName) {
      return 'No jobs were found to execute the selected checks';
    }
    if (isPartitioned) {
      return 'Executing checks on their own for partitioned assets is not yet supported';
    }
    return '';
  })();

  const onClick = async () => {
    if (!resolvedJobName) {
      return;
    }
    const executionParams: ExecutionParams = {
      mode: 'default',
      executionMetadata: {},
      runConfigData: '{}',
      selector: {
        jobName: resolvedJobName,
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

  if (additionalDropdownOptions && additionalDropdownOptions.length > 0) {
    return (
      <Box flex={{alignItems: 'center'}}>
        <Tooltip content={mainActionDisabledReason} canShow={!!mainActionDisabledReason}>
          <Button
            icon={iconEl}
            disabled={launching || !!mainActionDisabledReason}
            onClick={onClick}
            className={styles.executeChecksLeftButton}
          >
            {label}
          </Button>
        </Tooltip>
        <Popover
          isOpen={isDropdownOpen}
          onInteraction={(nextOpen) => setIsDropdownOpen(nextOpen)}
          position="bottom-right"
          content={
            <Menu>
              {additionalDropdownOptions.map((option) => {
                const item = (
                  <MenuItem
                    key={option.label}
                    text={option.label}
                    icon={option.icon}
                    onClick={option.onClick}
                    disabled={option.disabled}
                  />
                );
                return (
                  <Tooltip
                    canShow={option.disabled && !!option.disabledReason}
                    key={option.label}
                    content={option.disabledReason}
                    placement="left"
                  >
                    {item}
                  </Tooltip>
                );
              })}
            </Menu>
          }
        >
          <Button
            className={styles.executeChecksRightButton}
            icon={<Icon name="arrow_drop_down" />}
          />
        </Popover>
      </Box>
    );
  }

  return (
    <Tooltip content={mainActionDisabledReason} canShow={!!mainActionDisabledReason}>
      <Button icon={iconEl} disabled={!!mainActionDisabledReason || launching} onClick={onClick}>
        {label}
      </Button>
    </Tooltip>
  );
};

export const EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT = gql`
  fragment ExecuteChecksButtonCheckFragment on AssetCheck {
    name
    canExecuteIndividually
    jobNames
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
