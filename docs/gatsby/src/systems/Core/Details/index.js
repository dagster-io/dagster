/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'

export const Details = ({ children, ...props }) => {
  return (
    <dl sx={styles.wrapper} {...props}>
      {children}
    </dl>
  )
}
