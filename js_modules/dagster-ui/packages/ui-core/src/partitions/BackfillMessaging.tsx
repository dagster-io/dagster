import {Alert, ButtonLink, Colors, Group, Mono} from '@dagster-io/ui-components';
import * as React from 'react';

import {gql, useQuery} from '../apollo-client';
import {
  DaemonNotRunningAlertInstanceFragment,
  DaemonNotRunningAlertQuery,
  DaemonNotRunningAlertQueryVariables,
  UsingDefaultLauncherAlertInstanceFragment,
} from './types/BackfillMessaging.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {LaunchPartitionBackfillMutation} from '../instance/backfill/types/BackfillUtils.types';
import {getBackfillPath} from '../runs/RunsFeedUtils';
import {AnchorButton} from '../ui/AnchorButton';

const DEFAULT_RUN_LAUNCHER_NAME = 'DefaultRunLauncher';

function messageForLaunchBackfillError(data: LaunchPartitionBackfillMutation | null | undefined) {
  const result = data?.launchPartitionBackfill;

  let errors: React.ReactNode = undefined;
  if (result?.__typename === 'PythonError' || result?.__typename === 'PartitionSetNotFoundError') {
    errors = <PythonErrorInfo error={result} />;
  } else if (result?.__typename === 'InvalidStepError') {
    errors = <div>{`无效的步骤: ${result.invalidStepKey}`}</div>;
  } else if (result?.__typename === 'InvalidOutputError') {
    errors = <div>{`无效的输出: ${result.invalidOutputName} (步骤 ${result.stepKey})`}</div>;
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
      <div>发生意外错误。此回填未启动。</div>
      {errors ? (
        <ButtonLink
          color={Colors.accentPrimary()}
          underline="always"
          onClick={() => {
            showCustomAlert({
              body: errors,
            });
          }}
        >
          查看错误
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

export async function showBackfillSuccessToast(backfillId: string) {
  const url = getBackfillPath(backfillId);
  await showSharedToaster({
    intent: 'success',
    message: (
      <div>
        已创建回填 <Mono>{backfillId}</Mono>
      </div>
    ),
    action: {
      type: 'custom',
      element: <AnchorButton to={url}>查看</AnchorButton>,
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
    title="回填守护进程未运行。"
    description={
      <div>
        请参阅{' '}
        <a
          href="https://docs.dagster.io/deployment/dagster-daemon"
          target="_blank"
          rel="noreferrer"
        >
          dagster-daemon 文档
        </a>{' '}
        了解如何部署 dagster-daemon 进程。
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
          不建议使用默认运行启动器 <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> 在没有队列运行协调器的情况下启动回填。
        </div>
      }
      description={
        <div>
          请检查 <code>dagster.yaml</code> 中的实例配置，配置{' '}
          <a
            href="https://docs.dagster.io/deployment/run-coordinator"
            target="_blank"
            rel="noreferrer"
          >
            队列运行协调器
          </a>{' '}
          或更适合启动大量作业的运行启动器。
        </div>
      }
    />
  ) : null;
