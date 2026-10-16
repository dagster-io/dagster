import {RunRowSkeleton} from './RunRowSkeleton';

type Props = {
  rows?: number;
};

export const RunsFeedSkeleton = ({rows = 10}: Props) => (
  <div>
    {Array.from({length: rows}, (_, index) => (
      <RunRowSkeleton key={index} />
    ))}
  </div>
);
