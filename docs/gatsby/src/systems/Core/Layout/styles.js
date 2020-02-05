import { theme as t } from 'utils/css'

export const main = {
  position: 'relative',
  maxWidth: '100vw',
  overflowX: 'hidden',
}

export const page = state => {
  const closed = !state.matches('showing')
  const transform = `translate(${closed ? '-180px' : 0})`

  return {
    display: 'flex',
    width: 'calc(100% + 180px)',
    transform: [transform, transform, 'none'],
    transition: 'transform .3s',
    height: '100%',
  }
}

export const content = state => {
  const closed = !state.matches('showing')
  return {
    flex: 1,
    mt: t('header.gutter'),

    maxWidth: [
      'calc(100% - 180px)',
      'calc(100% - 180px)',
      'calc(100% - 360px)',
    ],

    '::before': {
      zIndex: 9,
      position: 'absolute',
      display: ['block', 'block', 'none'],
      content: '""',
      top: 0,
      left: 0,
      width: '100%',
      height: t => t.header.gutter,
      bg: 'blue.3',
      transform: `translate(${closed ? 0 : '-100%'})`,
      transition: 'transform .3s',
    },

    ...(state.context.width < 1024 && {
      '::after': {
        display: 'block',
        position: 'absolute',
        content: '""',
        top: closed ? '-100%' : 0,
        left: 0,
        width: '100%',
        height: '100%',
        bg: 'white',
        opacity: closed ? 0 : 0.8,
        transition: 'all .3s',
      },
    }),
  }
}
