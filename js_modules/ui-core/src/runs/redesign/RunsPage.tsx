import {Box, NonIdealState} from '@dagster-io/ui-components';

export const RunsPage = () => {
  return (
    <Box padding={64}>
      <NonIdealState icon="run" title="Runs" description="Redesigned runs page placeholder…" />
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsPage;
