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
    expect(headerRow!).toHaveTextContent(/foobar/i);
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
    expect(headerRow!).toHaveTextContent(/foobar/i);
    expect(dataRow!).toHaveTextContent(/12/i);

    // Display unparseable text in a single stretched cell
    expect(invalidRow!.childNodes).toHaveLength(1);
    expect(invalidRow!).toHaveTextContent(/could not parse/i);
    expect(invalidRow!).toHaveTextContent(/{"foo": NaN, "bar": …/i);
  });
});
