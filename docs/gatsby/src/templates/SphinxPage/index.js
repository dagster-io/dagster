/** @jsx jsx */
import { jsx } from 'theme-ui'

import { Layout, SEO } from 'systems/Core'

import { ReactParser } from '../../systems/ReactParser'
import { TableOfContents } from './components/TableOfContents'
import * as styles from './styles'

const SphinxPage = ({ pageContext: ctx }) => {
  const { page } = ctx
  return (
    <Layout>
      <SEO title={page.title} />
      <main sx={styles.wrapper}>
        <div sx={styles.content}>
          <ReactParser tree={page.parsed} />
        </div>
        <TableOfContents>
          <ReactParser tree={page.tocParsed} />
        </TableOfContents>
      </main>
    </Layout>
  )
}

export default SphinxPage
