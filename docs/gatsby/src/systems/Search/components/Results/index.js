/** @jsx jsx */
import { jsx } from "theme-ui";
import * as styles from "./styles";

import * as hitComps from "./hitComps";
import algoliaLogo from "./algolia-logo.svg";
import { Index, Hits, connectStateResults } from "react-instantsearch-dom";
import { useVersion } from "systems/Version";

const AllResults = connectStateResults(
  ({ searchState: state, searchResults: res, children }) =>
    res && res.nbHits > 0 ? children : `No results for '${state.query}'`
);

const Stats = connectStateResults(
  ({ searchResults: res }) =>
    res && res.nbHits > 0 && `${res.nbHits} result${res.nbHits > 1 ? `s` : ``}`
);

export default function({ showing, indices, onClose }) {
  const { version } = useVersion();
  return (
    <div sx={styles.wrapper(showing)}>
      {indices.map(({ name, title, hitComp }) => {
        const getHitComponent = hitComps[hitComp];
        return (
          <Index key={name} indexName={name}>
            <header>
              <h3>{title}</h3>
              <span>
                <Stats />
              </span>
            </header>
            <AllResults>
              <Hits hitComponent={getHitComponent(onClose, version.current)} />
            </AllResults>
          </Index>
        );
      })}
      <div sx={styles.poweredBy}>
        Powered by <img src={algoliaLogo} sx={{ width: 80 }} />
      </div>
    </div>
  );
}
