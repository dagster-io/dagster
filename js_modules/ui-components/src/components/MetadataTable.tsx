import clsx from 'clsx';
import * as React from 'react';

import {Box} from './Box';
import {Table, TableProps} from './Table';
import styles from './css/MetadataTable.module.css';

export type MetadataTableRow = {key: string; label?: React.ReactNode; value: React.ReactNode};

interface Props {
  rows: (MetadataTableRow | null | undefined)[];
  spacing?: 0 | 2 | 4;
}

export const MetadataTable = (props: Props) => {
  const {rows, spacing = 4} = props;

  return (
    <table className={styles.styledTable}>
      <tbody>
        {rows.map((pair: MetadataTableRow | null | undefined) => {
          if (!pair) {
            return null;
          }
          const {key, label, value} = pair;
          return (
            <tr key={key}>
              <td>
                <Box padding={{vertical: spacing, right: 32}}>
                  <div className={styles.metadataKey}>{label ?? key}</div>
                </Box>
              </td>
              <td>
                <Box padding={{vertical: spacing}}>{value}</Box>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export const StyledTable = ({className, ...props}: React.HTMLAttributes<HTMLTableElement>) => (
  <table className={clsx(styles.styledTable, className)} {...props} />
);

export const MetadataTableWIP = ({
  className,
  ...props
}: TableProps & React.HTMLAttributes<HTMLTableElement>) => (
  <Table className={clsx(styles.metadataTableWIP, className)} {...props} />
);
