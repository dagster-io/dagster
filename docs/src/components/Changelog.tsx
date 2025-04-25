/**
 * Custom parsing of CHANGES.md MDX to construct anchor IDs via component injection.
 *
 * https://mdxjs.com/guides/injecting-components/#injecting-components
 *
 */

import Changes, {toc as ChangelogTOC} from '@site/../CHANGES.md';
import React, {useRef} from 'react';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';

const Changelog = () => {
  const lastParentId = useRef(null); // track parent ID for anchor construction

  return (
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
  );
};

export {Changelog, ChangelogTOC};
