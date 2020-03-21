/** @jsx jsx */
import { jsx } from "theme-ui";
import * as styles from "./styles";

import * as hitComps from "./hitComps";
import algoliaLogo from "./algolia-logo.svg";
import { Index, Hits, connectStateResults } from "react-instantsearch-dom";
import { useVersion } from "systems/Version";

// TODO: Fix this types: these are somehow opaque
const AllResults = connectStateResults<any>(
  ({ searchState: state, searchResults: res, children }) =>
    res && res.nbHits > 0 ? children : `No results for '${state.query}'`
);

// TODO: Fix this types: these are somehow opaque
const Stats = connectStateResults<any>(
  ({ searchResults: res }: any): any =>
    res && res.nbHits > 0 && `${res.nbHits} result${res.nbHits > 1 ? `s` : ``}`
);

type IndicesElement = {
  name: string;
  title: string;
  hitComp: string;
};

type ResultsProps = {
  showing?: boolean;
  indices: IndicesElement[];
  onClose: () => void;
};

const Results: React.FC<ResultsProps> = ({ showing, indices, onClose }) => {
  const { version } = useVersion();
  return (
    <div sx={styles.wrapper(showing)}>
      {indices.map(({ name, title, hitComp }) => {
        // TODO: Fix this, it shouldn't be accessed by index / string.
        const getHitComponent = (hitComps as Record<string, any>)[hitComp];
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
};

export default Results;
