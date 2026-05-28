import {render, screen} from '@testing-library/react';

import {StatusBar} from '../BackfillAssetPartitionsTable';

describe('StatusBar', () => {
  it('does not show 100% completed while partitions are still in progress', () => {
    render(<StatusBar targeted={364} inProgress={1} succeeded={362} failed={0} />);
    expect(screen.getByText('99% completed')).toBeInTheDocument();
  });

  it('shows 100% completed only when all targeted partitions are done', () => {
    render(<StatusBar targeted={364} inProgress={0} succeeded={364} failed={0} />);
    expect(screen.getByText('100% completed')).toBeInTheDocument();
  });

  it('counts failed partitions as completed', () => {
    render(<StatusBar targeted={100} inProgress={0} succeeded={90} failed={10} />);
    expect(screen.getByText('100% completed')).toBeInTheDocument();
  });

  it('floors fractional percentages instead of rounding up', () => {
    render(<StatusBar targeted={1000} inProgress={1} succeeded={998} failed={0} />);
    expect(screen.getByText('99% completed')).toBeInTheDocument();
  });

  it('shows 0% completed when nothing has finished', () => {
    render(<StatusBar targeted={10} inProgress={2} succeeded={0} failed={0} />);
    expect(screen.getByText('0% completed')).toBeInTheDocument();
  });
});
