import {Alert, ButtonLink, Colors, Group, Mono} from '@dagster-io/ui-components';
import {History} from 'history';
import * as React from 'react';

import {
  DaemonNotRunningAlertInstanceFragment,
  DaemonNotRunningAlertQuery,
  DaemonNotRunningAlertQueryVariables,
  UsingDefaultLauncherAlertInstanceFragment,
} from './types/BackfillMessaging.types';
import {gql, useQuery} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {LaunchPartitionBackfillMutation} from '../instance/backfill/types/BackfillUtils.types';
import {getBackfillPath} from '../runs/RunsFeedUtils';

const DEFAULT_RUN_LAUNCHER_NAME = 'DefaultRunLauncher';

function messageForLaunchBackfillError(data: LaunchPartitionBackfillMutation | null | undefined) {
  const result = data?.launchPartitionBackfill;

  let errors: React.ReactNode = undefined;
  if (result?.__typename === 'PythonError' || result?.__typename === 'PartitionSetNotFoundError') {
    errors = <PythonErrorInfo error={result} />;
  } else if (result?.__typename === 'InvalidStepError') {
    errors = <div>{`Invalid step: ${result.invalidStepKey}`}</div>;
  } else if (result?.__typename === 'InvalidOutputError') {
    errors = <div>{`Invalid output: ${result.invalidOutputName} for ${result.stepKey}`}</div>;
  } else if (result && 'errors' in result) {
    errors = (
      <>
        {result['errors'].map((error, idx) => (
          <PythonErrorInfo error={error} key={idx} />
        ))}
      </>
    );
  }

  return (
    <Group direction="column" spacing={4}>
      <div>An unexpected error occurred. This backfill was not launched.</div>
      {errors ? (
        <ButtonLink
          color={Colors.accentReversed()}
          underline="always"
          onClick={() => {
            showCustomAlert({
              body: errors,
            });
          }}
        >
          View error
        </ButtonLink>
      ) : null}
    </Group>
  );
}

export async function showBackfillErrorToast(
  data: LaunchPartitionBackfillMutation | null | undefined,
) {
  await showSharedToaster({
    message: messageForLaunchBackfillError(data),
    icon: 'error',
    intent: 'danger',
  });
}

export async function showBackfillSuccessToast(
  history: History<unknown>,
  backfillId: string,
  isAssetBackfill: boolean,
) {
  const url = getBackfillPath(backfillId, isAssetBackfill);
  const [pathname, search] = url.split('?');
  await showSharedToaster({
    intent: 'success',
    message: (
      <div>
        Created backfill <Mono>{backfillId}</Mono>
      </div>
    ),
    action: {
      text: 'View',
      href: history.createHref({pathname, search}),
    },
  });
}

export const DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT = gql`
  fragment DaemonNotRunningAlertInstanceFragment on Instance {
    id
    daemonHealth {
      id
      daemonStatus(daemonType: "BACKFILL") {
        id
        healthy
      }
    }
  }
`;

const DAEMON_NOT_RUNNING_ALERT_QUERY = gql`
  query DaemonNotRunningAlertQuery {
    instance {
      id
      ...DaemonNotRunningAlertInstanceFragment
    }
  }

  ${DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT}
`;

export function isBackfillDaemonHealthy(instance: DaemonNotRunningAlertInstanceFragment) {
  return instance.daemonHealth.daemonStatus.healthy;
}

export function useIsBackfillDaemonHealthy() {
  const queryData = useQuery<DaemonNotRunningAlertQuery, DaemonNotRunningAlertQueryVariables>(
    DAEMON_NOT_RUNNING_ALERT_QUERY,
    {blocking: false},
  );
  return queryData.data ? isBackfillDaemonHealthy(queryData.data.instance) : true;
}

export const DaemonNotRunningAlert = () => (
  <Alert
    intent="warning"
    title="The backfill daemon is not running."
    description={
      <div>
        See the{' '}
        <a
          href="https://docs.dagster.io/deployment/dagster-daemon"
          target="_blank"
          rel="noreferrer"
        >
          dagster-daemon documentation
        </a>{' '}
        for more information on how to deploy the dagster-daemon process.
      </div>
    }
  />
);

export const USING_DEFAULT_LAUNCHER_ALERT_INSTANCE_FRAGMENT = gql`
  fragment UsingDefaultLauncherAlertInstanceFragment on Instance {
    id
    runQueuingSupported
    runLauncher {
      name
    }
  }
`;

export const UsingDefaultLauncherAlert = ({
  instance,
}: {
  instance: UsingDefaultLauncherAlertInstanceFragment;
}) =>
  instance.runLauncher?.name === DEFAULT_RUN_LAUNCHER_NAME && !instance.runQueuingSupported ? (
    <Alert
      intent="warning"
      title={
        <div>
          Using the default run launcher <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> to launch
          backfills without a queued run coordinator is not advised.
        </div>
      }
      description={
        <div>
          Check your instance configuration in <code>dagster.yaml</code> to configure the{' '}
          <a
            href="https://docs.dagster.io/deployment/run-coordinator"
            target="_blank"
            rel="noreferrer"
          >
            queued run coordinator
          </a>{' '}
          or a run launcher more appropriate for launching a large number of jobs.
        </div>
      }
    />
  ) : null;
