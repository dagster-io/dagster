import {Box} from '../Box';
import {CursorHistoryControls, CursorPaginationControls} from '../CursorControls';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'CursorControls',
  component: CursorPaginationControls,
};

const noop = () => {};

export const BothEnabled = () => {
  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <CursorPaginationControls
        hasPrevCursor
        hasNextCursor
        popCursor={noop}
        advanceCursor={noop}
        reset={noop}
      />
    </Box>
  );
};

export const DisabledStates = () => {
  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <CursorPaginationControls
        hasPrevCursor={false}
        hasNextCursor
        popCursor={noop}
        advanceCursor={noop}
        reset={noop}
      />
      <CursorPaginationControls
        hasPrevCursor
        hasNextCursor={false}
        popCursor={noop}
        advanceCursor={noop}
        reset={noop}
      />
      <CursorPaginationControls
        hasPrevCursor={false}
        hasNextCursor={false}
        popCursor={noop}
        advanceCursor={noop}
        reset={noop}
      />
    </Box>
  );
};

export const HistoryVariant = () => {
  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <CursorHistoryControls
        hasPrevCursor
        hasNextCursor
        popCursor={noop}
        advanceCursor={noop}
        reset={noop}
      />
    </Box>
  );
};
