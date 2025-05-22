/**
 * Custom parsing of CHANGES.md MDX to construct anchor IDs via component injection.
 *
 * https://mdxjs.com/guides/injecting-components/#injecting-components
 *
 */

import Changes, {toc as originalTOC} from '@site/../CHANGES.md';
import React, {useRef, useMemo} from 'react';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';

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
      return {
        ...item,
        id: `${currentH2Id}-${item.id}`,
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
            const h3Id = properties.id;
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
