export const wrapper = {
  p: 4,
  bg: 'lightGray.3',
  borderRadius: 'radius',
  border: t => `1px solid ${t.colors.lightGray[1]}`,

  '.field-list': {
    p: 4,
    bg: 'white',
    borderRadius: 'radius',
    border: t => `1px solid ${t.colors.lightGray[1]}`,
  },

  'dt.field-odd': {
    display: 'flex',
    alignItems: 'center',
    textTransform: 'uppercase',
    fontSize: 2,
    color: 'dark.3',
    mb: 3,
  },

  'dd.field-odd': {
    m: 0,
  },

  'dd.field-odd > ul': {
    mb: 0,
    fontSize: 2,
  },
}
