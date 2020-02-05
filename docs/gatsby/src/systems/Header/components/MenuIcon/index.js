/** @jsx jsx */
import { jsx } from 'theme-ui'

const iconStyle = opened => ({
  width: '30px',
  height: '28px',
  position: 'relative',
  transform: 'rotate(0deg)',
  transition: '.5s ease-in-out',
  cursor: 'pointer',

  span: {
    display: 'block',
    position: 'absolute',
    height: '3px',
    width: '100%',
    bg: 'gray.4',
    borderRadius: '9px',
    opacity: '1',
    left: '0',
    transform: 'rotate(0deg)',
    transition: 'all .25s ease-in-out',
  },

  'span:nth-of-type(1)': {
    top: '2px',
  },
  'span:nth-of-type(2)': {
    top: '12px',
  },
  'span:nth-of-type(3)': {
    top: '12px',
  },
  'span:nth-of-type(4)': {
    top: '22px',
  },

  ...(opened && {
    'span:nth-of-type(1)': {
      top: '10px',
      width: '0%',
      left: '50%',
    },
    'span:nth-of-type(2)': {
      top: 12,
      transform: 'rotate(45deg)',
    },
    'span:nth-of-type(3)': {
      top: 12,
      transform: 'rotate(-45deg)',
    },
    'span:nth-of-type(4)': {
      top: '10px',
      width: '0%',
      left: '50%',
    },
  }),
})

export const MenuIcon = ({ opened }) => {
  return (
    <div id="menu-icon" sx={iconStyle(opened)}>
      <span id="menu-icon-span"></span>
      <span id="menu-icon-span"></span>
      <span id="menu-icon-span"></span>
      <span id="menu-icon-span"></span>
    </div>
  )
}
