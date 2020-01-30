/** @jsx jsx */
import { jsx } from 'theme-ui'
import { forwardRef, useEffect, useRef } from 'react'
import { Search, Slack, GitHub } from 'react-feather'
import { useMachine } from '@xstate/react'
import useClickAway from 'react-use/lib/useClickAway'
import useKeyPressEvent from 'react-use/lib/useKeyPressEvent'
import useWindowSize from 'react-use/lib/useWindowSize'

import { ExternalLink, Menu, Logo } from 'systems/Core'

import { MenuIcon } from './components/MenuIcon'
import { headerMachine } from './machines/header'
import * as styles from './styles'

export const Header = forwardRef(({ onMenuClick, sidebarOpened }, ref) => {
  const searchRef = useRef(null)
  const { width } = useWindowSize()
  const [state, send] = useMachine(
    headerMachine.withContext({
      width,
      value: '',
    }),
  )

  const { value } = state.context
  const showing = state.matches('opened')

  function handleToggle() {
    send('TOGGLE')
  }

  function handleChangeValue(ev) {
    send('CHANGE', { data: ev.target.value })
  }

  useEffect(() => {
    send('SET_INITIAL_WIDTH', { data: width })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    send('SET_WIDTH', { data: width })
  }, [width, send])

  useKeyPressEvent('Escape', () => {
    if (showing) handleToggle()
  })

  useClickAway(searchRef, () => {
    if (showing) handleToggle()
  })

  return (
    <header ref={ref} sx={styles.wrapper}>
      <div sx={styles.right}>
        <button sx={styles.menuBtn(showing)} onClick={onMenuClick}>
          <MenuIcon opened={sidebarOpened} />
        </button>
        <Logo sx={styles.logo(showing)} />
        <div ref={searchRef} sx={styles.search(showing)}>
          <Search size={35} onClick={handleToggle} />
          <input
            placeholder="Search here..."
            onChange={handleChangeValue}
            value={value}
          />
        </div>
      </div>
      <Menu sx={styles.socialIcons(showing)}>
        <ExternalLink href="#">
          <Slack sx={{ fill: 'blue.3' }} />
        </ExternalLink>
        <ExternalLink href="#">
          <GitHub />
        </ExternalLink>
      </Menu>
    </header>
  )
})
