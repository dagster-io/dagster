import { theme as t } from 'utils/css'

export const wrapper = {
  zIndex: 9,
  position: 'relative',
  px: 3,
  width: 180,
  minHeight: '100vh',
  bg: 'sidebar.bg',
  color: 'sidebar.color',
  textAlign: 'right',

  '.toctree-wrapper': {
    fontFamily: 'heading',
    fontWeight: 500,
  },

  '.toctree-wrapper ul': {
    m: 0,
    p: 0,
    listStyle: 'none',
    color: 'white',
  },
}

export const active = (hasActive, top) => ({
  position: 'absolute',
  width: 4,
  height: 25,
  bg: 'white',
  borderRadius: 'rounded',
  opacity: hasActive ? 1 : 0,
  top: 0,
  right: '3px',
  transform: `translateY(${top - 3}px)`,
  transition: 'transform .2s cubic-bezier(.25,.75,.5,1.25)',
})

export const content = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-end',
  height: '100%',
  maxHeight: '100vh',
  pt: t('header.gutter'),
}

export const menu = {
  mb: 4,
}
