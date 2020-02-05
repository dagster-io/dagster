/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'

export const Table = props => {
  return <table {...props} sx={styles} />
}
