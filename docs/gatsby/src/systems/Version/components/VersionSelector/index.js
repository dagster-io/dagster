/** @jsx jsx */
import { jsx } from 'theme-ui'

import * as styles from './styles'
import { useVersion } from 'systems/Version'

export const VersionSelector = () => {
  const { version, setCurrent } = useVersion()

  const handleChange = ev => {
    setCurrent(ev.target.value)
  }

  return (
    <select sx={styles.wrapper} onChange={handleChange} value={version.current}>
      {version.all.map(vs => (
        <option key={vs} value={vs}>
          {vs}
        </option>
      ))}
    </select>
  )
}
