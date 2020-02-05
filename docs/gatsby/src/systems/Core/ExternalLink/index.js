/** @jsx jsx */
import { jsx } from 'theme-ui'

export const ExternalLink = ({ href, children, ...props }) => {
  return (
    <a
      sx={{ display: 'flex', alignItems: 'center' }}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  )
}
