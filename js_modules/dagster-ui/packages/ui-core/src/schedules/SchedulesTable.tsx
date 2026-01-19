import {Box, Popover, Tag} from '@dagster-io/ui-components';

import {InstigationStatus} from '../graphql/types';

export const errorDisplay = (status: InstigationStatus, runningScheduleCount: number) => {
  if (status === InstigationStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === InstigationStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === InstigationStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      '定时任务已设置为运行状态，但调度器未配置或未运行此任务',
    );
  } else if (status === InstigationStatus.STOPPED && runningScheduleCount > 0) {
    errors.push('定时任务已设置为停止状态，但调度器仍在运行此任务');
  }

  if (runningScheduleCount > 0) {
    errors.push('发现重复的定时任务 cron 作业。');
  }

  return (
    <Popover
      interactionKind="hover"
      popoverClassName="bp5-popover-content-sizing"
      position="right"
      content={
        <Box flex={{direction: 'column', gap: 8}} padding={12}>
          <strong>此定时任务存在错误。</strong>
          <div>错误：</div>
          <ul>
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Box>
      }
    >
      <Tag interactive intent="danger">
        错误
      </Tag>
    </Popover>
  );
};
