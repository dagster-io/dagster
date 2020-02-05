/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'

export const List = ({ children, ...props }) => {
  return (
    <li sx={styles.wrapper} {...props}>
      {children}
    </li>
  )
}
