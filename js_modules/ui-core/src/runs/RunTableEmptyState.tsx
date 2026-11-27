import {Box, Icon, NonIdealState} from '@dagster-io/ui-components';

import {AnchorButton} from '../ui/AnchorButton';

type Props = {
  anyFilter: boolean;
  shrinkable?: boolean;
};

export const RunTableEmptyState = ({anyFilter, shrinkable}: Props) => {
  return (
    <div>
      <Box margin={{vertical: 32}}>
        {anyFilter ? (
          <NonIdealState
            icon="run"
            shrinkable={shrinkable}
            title="No matching runs"
            description="No runs were found for this filter."
          />
        ) : (
          <NonIdealState
            icon="run"
            shrinkable={shrinkable}
            title="No runs found"
            description={
              <Box flex={{direction: 'column', gap: 12}}>
                <div>You have not launched any runs yet.</div>
                <Box flex={{direction: 'row', gap: 12, alignItems: 'center', wrap: 'wrap'}}>
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
