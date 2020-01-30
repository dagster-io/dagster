/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'

export const Menu = ({ children, gap = 3, vertical, ...props }) => {
  return (
    <div sx={styles.wrapper(gap, vertical)} {...props}>
      {children}
    </div>
  )
}
