/** @jsx jsx */
import { Styled, jsx } from 'theme-ui'
import { forwardRef } from 'react'
import { Link as BaseLink } from 'gatsby'
import { Location } from '@reach/router'
import path from 'path-browserify'

import * as styles from './styles'

export const Link = forwardRef(({ href, to, ...props }, ref) => {
  const isExternal = href && href.startsWith('http')

  return isExternal ? (
    // eslint-disable-next-line jsx-a11y/anchor-has-content
    <Styled.a href={href} sx={styles.wrapper} {...props} />
  ) : (
    <Location>
      {({ location }) => (
        <BaseLink
          ref={ref}
          activeClassName="active"
          sx={styles.wrapper}
          to={
            href && !isExternal
              ? `${path.resolve(location.pathname, href)}`
              : to
          }
          {...props}
        />
      )}
    </Location>
  )
})
