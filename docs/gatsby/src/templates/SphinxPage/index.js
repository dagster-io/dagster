/** @jsx jsx */
import { jsx } from "theme-ui";
import { useState } from "react";
import { FileText, ArrowLeft, ArrowRight, Home } from "react-feather";
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
          <ul sx={styles.breadcrumb}>
            <li>
              <Link to="/">
                <Home size={17} />
              </Link>
            </li>
            {page.parents &&
              Boolean(page.parents.length) &&
              page.parents.map((item, idx) => {
                return (
                  <li>
                    <Link key={idx} to={item.link} isNav>
                      {item.title}
                    </Link>
                  </li>
                );
              })}
            <li className="current">{page.title}</li>
          </ul>
          {isMobile && (
            <button sx={styles.btnShowToc} onClick={handleShowToc}>
              <FileText sx={styles.icon} size={14} />
              Show contents
            </button>
          )}
          <ReactParser tree={page.parsed} />
          <div sx={styles.pageLinks}>
            {page.prev && (
              <Link to={page.prev.link} isNav>
                <ArrowLeft className="left" size={20} />
                {page.prev.title}
              </Link>
            )}
            {page.next && (
              <Link to={page.next.link} isNav>
                {page.next.title}
                <ArrowRight className="right" size={20} />
              </Link>
            )}
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
