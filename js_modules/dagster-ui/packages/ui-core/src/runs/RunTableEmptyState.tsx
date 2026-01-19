import {Box, Icon, NonIdealState} from '@dagster-io/ui-components';

import {AnchorButton} from '../ui/AnchorButton';

export const RunTableEmptyState = ({anyFilter}: {anyFilter: boolean}) => {
  return (
    <div>
      <Box margin={{vertical: 32}}>
        {anyFilter ? (
          <NonIdealState
            icon="run"
            title="无匹配的运行"
            description="未找到符合此筛选条件的运行。"
          />
        ) : (
          <NonIdealState
            icon="run"
            title="暂无运行"
            description={
              <Box flex={{direction: 'column', gap: 12}}>
                <div>您尚未启动任何运行。</div>
                <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                  <AnchorButton icon={<Icon name="add_circle" />} to="/overview/jobs">
                    启动运行
                  </AnchorButton>
                  <span>或</span>
                  <AnchorButton icon={<Icon name="materialization" />} to="/asset-groups">
                    物化资产
                  </AnchorButton>
                </Box>
              </Box>
            }
          />
        )}
      </Box>
    </div>
  );
};
