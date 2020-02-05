/** @jsx jsx */
import './index.css'

import { jsx, Styled } from 'theme-ui'
import { useRef, useEffect } from 'react'
import { Location } from '@reach/router'
import { useMachine } from '@xstate/react'
import useClickAway from 'react-use/lib/useClickAway'
import useKeyPressEvent from 'react-use/lib/useKeyPressEvent'
import useWindowSize from 'react-use/lib/useWindowSize'
import PropTypes from 'prop-types'

import { Sidebar } from 'systems/Sidebar'
import { Header } from 'systems/Header'
import { VersionProvider } from 'systems/Version'

import { responsiveMachine } from './machines/responsive'
import * as styles from './styles'

export const Layout = ({ children }) => {
  const sidebarRef = useRef(null)
  const { width } = useWindowSize()
  const [state, send] = useMachine(responsiveMachine)
  const showing = state.matches('showing')

  function handleToggle() {
    send('TOGGLE')
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

  useClickAway(sidebarRef, ev => {
    const { id } = ev.target
    if (id !== 'menu-icon' && id !== 'menu-icon-span' && showing) {
      handleToggle()
    }
  })

  return (
    <Location>
      {({ location }) => (
        <VersionProvider>
          <Styled.root>
            <main sx={styles.main}>
              <Header
                ref={sidebarRef}
                onMenuClick={handleToggle}
                sidebarOpened={showing}
              />
              <div sx={styles.page(state)}>
                <Sidebar
                  ref={sidebarRef}
                  location={location}
                  onLinkClick={handleToggle}
                />
                <div sx={styles.content(state)}>{children}</div>
              </div>
            </main>
          </Styled.root>
        </VersionProvider>
      )}
    </Location>
  )
}

Layout.propTypes = {
  children: PropTypes.node.isRequired,
}
