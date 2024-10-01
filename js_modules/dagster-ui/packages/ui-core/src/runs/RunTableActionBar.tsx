import {Box, Colors} from '@dagster-io/ui-components';

export function RunTableActionBar({
  top,
  bottom,
  sticky,
}: {
  top: React.ReactNode;
  bottom?: React.ReactNode;
  sticky?: boolean;
}) {
  return (
    <Box
      flex={{direction: 'column'}}
      padding={{vertical: 12}}
      style={
        sticky
          ? {position: 'sticky', top: 0, background: Colors.backgroundDefault(), zIndex: 2}
          : {}
      }
    >
      <Box flex={{alignItems: 'center', gap: 12}} padding={{horizontal: 24}}>
        {top}
      </Box>
      {bottom ? (
        <Box
          margin={{top: 12}}
          padding={{horizontal: 24, top: 8}}
          border="top"
          flex={{gap: 8, wrap: 'wrap'}}
        >
          {bottom}
        </Box>
      ) : null}
    </Box>
  );
}
