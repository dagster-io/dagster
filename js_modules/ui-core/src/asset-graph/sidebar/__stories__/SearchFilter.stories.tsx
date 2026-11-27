import {Box, Text} from '@dagster-io/ui-components';
import * as React from 'react';

import {buildAssetKey, buildAssetNode} from '../../../graphql/builders';
import {buildGraphData} from '../../Utils';
import {SearchFilter} from '../SearchFilter';
import {buildSidebarSearchValues} from '../searchValues';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Graph/Sidebar SearchFilter',
  component: SearchFilter,
};

// Values are built through buildSidebarSearchValues rather than hand-written so
// these stories exercise the same label/path derivation and ordering the
// sidebar uses in production.
function searchValuesFor(paths: string[][]) {
  return buildSidebarSearchValues(
    buildGraphData(
      paths.map((path) =>
        buildAssetNode({
          id: JSON.stringify(path),
          assetKey: buildAssetKey({path}),
          dependencyKeys: [],
          dependedByKeys: [],
        }),
      ),
    ).nodes,
  );
}

// The sidebar is a narrow column, so render at a comparable width to see how
// the disambiguating path behaves in the space it actually gets.
const SIDEBAR_WIDTH = 292;

const Example = ({paths, caption}: {paths: string[][]; caption: string}) => {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const [selected, setSelected] = React.useState<string | null>(null);
  const values = React.useMemo(() => searchValuesFor(paths), [paths]);

  // Suggest opens its menu on focus, so focus the input to show the list
  // without the reader having to click into it.
  React.useEffect(() => {
    containerRef.current?.querySelector('input')?.focus();
  }, []);

  return (
    <Box flex={{direction: 'column', gap: 8}} padding={24}>
      <Text size={14} color="textLight" as="div">
        {caption}
      </Text>
      <div ref={containerRef} style={{width: SIDEBAR_WIDTH}}>
        <SearchFilter values={values} onSelectValue={(_e, value) => setSelected(value)} />
      </div>
      <Text size={12} color="textLighter" as="div">
        {selected ? `Selected: ${selected}` : 'Nothing selected yet.'}
      </Text>
      {/* Room for the menu to expand into. */}
      <div style={{height: 320}} />
    </Box>
  );
};

export const DistinctLabels = () => (
  <Example
    caption="Every asset has a unique leaf name, so no paths are shown."
    paths={[['customers'], ['orders'], ['payments'], ['shipments']]}
  />
);

export const DuplicateLabels = () => (
  <Example
    caption={
      'Three assets are named `orders` in different namespaces. Each shows its ' +
      'namespace so they can be told apart; `inventory` is unique and stays bare.'
    }
    paths={[
      ['raw', 'orders'],
      ['staging', 'orders'],
      ['marts', 'orders'],
      ['raw', 'inventory'],
    ]}
  />
);

export const LongPaths = () => (
  <Example
    caption={
      'Deeply nested keys, to check the namespace still reads in the sidebar’s ' +
      'width without crowding out the label.'
    }
    paths={[
      ['analytics', 'warehouse', 'staging', 'daily_revenue'],
      ['analytics', 'warehouse', 'marts', 'daily_revenue'],
      ['analytics', 'ingest', 'daily_revenue'],
    ]}
  />
);

export const SearchableByNamespace = () => (
  <Example
    caption={
      'Type `raw` to match on the namespace, or `orders` to match on the label — ' +
      'the predicate checks the fully-qualified key as well as the display name.'
    }
    paths={[
      ['raw', 'orders'],
      ['raw', 'customers'],
      ['staging', 'orders'],
      ['staging', 'customers'],
    ]}
  />
);
