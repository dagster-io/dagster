export const wrapper = (gap, vertical) => ({
  display: 'inline-grid',
  gridGap: gap,
  gridAutoFlow: vertical ? 'row' : 'column',
})
