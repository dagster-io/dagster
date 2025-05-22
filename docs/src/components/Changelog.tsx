/**
 * Custom parsing of CHANGES.md MDX to construct anchor IDs via component injection.
 *
 * This was created to resolve an issue with anchor tags in the `/about/changelog` page where
+ * subheaders like `## New` or `## Bugfixes` would create incremental tags like `new-1` and `new-2`.
 * This was a problem because on each release the `new-1` would change, and break existing anchors.
 *
 * https://mdxjs.com/guides/injecting-components/#injecting-components
 *
 */

import Changes, {toc as originalTOC} from '@site/../CHANGES.md';
import React, {useRef, useMemo} from 'react';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';

/**
 * Normalizes ID for use in anchor tag; removes appended index as this makes IDs subject to side-effects.
 */
function normalizeId(id: string) {
  return id.replace(/-\d+$/, '');
}

// Create transformed TOC that matches our custom anchor structure
const transformedTOC = (() => {
  // Deep clone the original TOC to avoid mutations
  const newTOC = JSON.parse(JSON.stringify(originalTOC));

  let currentH2Id = null;
  return newTOC.map((item) => {
    if (item.level === 2) {
      currentH2Id = item.id;
      return item;
    }

    if (item.level === 3 && currentH2Id) {
      const id = normalizeId(item.id);
      return {
        ...item,
        id: `${currentH2Id}-${id}`,
      };
    }

    return item;
  });
})();

const Changelog = () => {
  const lastParentId = useRef(null); // track parent ID for anchor construction

  return (
    <>
      <Changes
        components={{
          h2(properties) {
            lastParentId.current = properties.id; // update the ref when an h2 is rendered
            return <Heading as="h2" {...properties} />;
          },
          h3(properties) {
            const h3Id = normalizeId(properties.id);
            const combinedId = lastParentId.current ? `${lastParentId.current}-${h3Id}` : h3Id;
            return (
              <Heading as="h3" {...properties} id={combinedId}>
                {properties.children}
              </Heading>
            );
          },
        }}
      />
    </>
  );
};

// Export the transformed TOC instead of the original
export {Changelog, transformedTOC as ChangelogTOC};
