import {Box, Checkbox} from '@dagster-io/ui-components';

import {AllAssetNodeFacets, labelForFacet} from './AssetNodeFacets';
import {AssetNodeFacet} from './AssetNodeFacetsUtil';

export const AssetNodeFacetsPicker = ({
  value,
  onChange,
}: {
  value: Set<AssetNodeFacet>;
  onChange: (v: Set<AssetNodeFacet>) => void;
}) => {
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {AllAssetNodeFacets.map((facet) => (
        <Checkbox
          key={facet}
          checked={value.has(facet)}
          label={labelForFacet(facet)}
          onChange={(e) =>
            onChange(
              new Set(
                e.currentTarget.checked
                  ? [...value, facet]
                  : Array.from(value).filter((v) => v !== facet),
              ),
            )
          }
        />
      ))}
    </Box>
  );
};
