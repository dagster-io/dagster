import {render, screen} from '@testing-library/react';

import {
  buildTable,
  buildTableColumn,
  buildTableMetadataEntry,
  buildTableSchema,
} from '../../graphql/types';
import {TableMetadataEntryComponent} from '../MetadataEntry';

describe('TableMetadataEntryComponent', () => {
  it('renders a metadata table for the supplied records', async () => {
    const entry = buildTableMetadataEntry({
      label: 'hello world',
      description: 'describe world',
      table: buildTable({
        records: ['{"foo": 1, "bar": 2}'],
        schema: buildTableSchema({
          columns: [buildTableColumn({name: 'foo'}), buildTableColumn({name: 'bar'})],
        }),
      }),
    });

    render(<TableMetadataEntryComponent entry={entry} />);
    const rows = await screen.findAllByRole('row');
    expect(rows).toHaveLength(2);
    const [headerRow, dataRow] = rows;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(headerRow!).toHaveTextContent(/foobar/i);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(dataRow!).toHaveTextContent(/12/i);
  });

  it('renders an unparseable row', async () => {
    const entry = buildTableMetadataEntry({
      label: 'hello world',
      description: 'describe world',
      table: buildTable({
        records: ['{"foo": 1, "bar": 2}', '{"foo": NaN, "bar": NaN}'],
        schema: buildTableSchema({
          columns: [buildTableColumn({name: 'foo'}), buildTableColumn({name: 'bar'})],
        }),
      }),
    });

    render(<TableMetadataEntryComponent entry={entry} />);
    const rows = await screen.findAllByRole('row');
    expect(rows).toHaveLength(3);
    const [headerRow, dataRow, invalidRow] = rows;

    // Display parseable rows as expected
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(headerRow!).toHaveTextContent(/foobar/i);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(dataRow!).toHaveTextContent(/12/i);

    // Display unparseable text in a single stretched cell
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(invalidRow!.childNodes).toHaveLength(1);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(invalidRow!).toHaveTextContent(/could not parse/i);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(invalidRow!).toHaveTextContent(/{"foo": NaN, "bar": …/i);
  });
});
