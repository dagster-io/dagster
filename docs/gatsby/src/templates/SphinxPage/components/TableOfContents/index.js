/** @jsx jsx */
import { jsx } from 'theme-ui'
import { FileText } from 'react-feather'
import Sticky from 'react-stickynode'

import * as styles from './styles'

export const TableOfContents = ({ children }) => {
  return (
    <div sx={styles.wrapper}>
      <Sticky enabled={true} top={30}>
        <h2 sx={styles.title}>
          <FileText sx={styles.icon} size={14} />
          Contents
        </h2>
        {children}
      </Sticky>
    </div>
  )
}
