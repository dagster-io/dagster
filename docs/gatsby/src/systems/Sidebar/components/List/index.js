/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'

export const isToctreeLi = ({ name, value }) => {
  return name === 'class' && value.startsWith('toctree')
}

export const isSidebarList = node => {
  return node.tagName === 'li' && node.attrs.some(isToctreeLi)
}

export const List = ({ children, ...props }) => {
  return (
    <li sx={styles.wrapper} {...props}>
      {children}
    </li>
  )
}
