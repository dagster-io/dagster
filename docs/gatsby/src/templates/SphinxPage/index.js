/** @jsx jsx */
import { jsx } from "theme-ui";
import { useState } from "react";
import { FileText, ArrowLeft, ArrowRight } from "react-feather";
import useWindowSize from "react-use/lib/useWindowSize";

import { Layout, SEO, Link } from "systems/Core";

import { ReactParser } from "../../systems/ReactParser";
import { TableOfContents } from "./components/TableOfContents";
import * as styles from "./styles";

const SphinxPage = ({ pageContext: ctx }) => {
  const { page } = ctx;
  const { width } = useWindowSize();
  const [showToc, setShowToc] = useState(false);
  const isMobile = width < 1024;

  function handleShowToc() {
    setShowToc(s => !s);
  }

  function handleCloseToc() {
    setShowToc(false);
  }

  return (
    <Layout>
      <SEO title={page.title} />
      <main sx={styles.wrapper}>
        <div sx={styles.content}>
          {isMobile && (
            <button sx={styles.btnShowToc} onClick={handleShowToc}>
              <FileText sx={styles.icon} size={14} />
              Show contents
            </button>
          )}
          <ReactParser tree={page.parsed} />
          <div sx={styles.pageLinks}>
            <Link to={page.prev.link} isNav sx={styles.prevLink}>
              <ArrowLeft className="left" size={20} />
              {page.prev.title}
            </Link>
            <Link to={page.next.link} isNav sx={styles.nextLink}>
              {page.next.title}
              <ArrowRight className="right" size={20} />
            </Link>
          </div>
        </div>
        <TableOfContents
          isMobile={isMobile}
          opened={showToc}
          onClose={handleCloseToc}
        >
          <ReactParser tree={page.tocParsed} />
        </TableOfContents>
      </main>
    </Layout>
  );
};

export default SphinxPage;
