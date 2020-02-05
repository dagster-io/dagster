/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'

export const Heading = ({ tagName: Component, ...props }) => {
  return <Component sx={styles.wrapper(Component)} {...props} />
}
