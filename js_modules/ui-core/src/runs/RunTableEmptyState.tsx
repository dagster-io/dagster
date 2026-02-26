import {Box, Icon, NonIdealState} from '@dagster-io/ui-components';

import {AnchorButton} from '../ui/AnchorButton';

export const RunTableEmptyState = ({anyFilter}: {anyFilter: boolean}) => {
  return (
    <div>
      <Box margin={{vertical: 32}}>
        {anyFilter ? (
          <NonIdealState
            icon="run"
            title="No matching runs"
            description="No runs were found for this filter."
          />
        ) : (
          <NonIdealState
            icon="run"
            title="No runs found"
            description={
              <Box flex={{direction: 'column', gap: 12}}>
                <div>You have not launched any runs yet.</div>
                <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                  <AnchorButton icon={<Icon name="add_circle" />} to="/overview/jobs">
                    Launch a run
                  </AnchorButton>
                  <span>or</span>
                  <AnchorButton icon={<Icon name="materialization" />} to="/asset-groups">
                    Materialize an asset
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
