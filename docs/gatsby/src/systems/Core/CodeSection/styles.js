const border = t => {
  return `1px solid ${t.colors.lightGray[1]}`
}

export const wrapper = {
  fontFamily: 'mono',
  my: [3, 3, 4],

  // --------------------------------
  // Code file
  // --------------------------------
  '.code-file': {
    bg: 'gray.1',
    fontFamily: 'mono',
    fontSize: 1,
    p: 3,
    py: 2,
    color: 'lightGray.1',
  },

  '.code-file .permalink': {
    display: 'none',
  },

  // --------------------------------
  // Code block
  // --------------------------------
  '.code-block': {
    border,
    display: 'flex',
  },
  '.code-block > pre': {
    borderRadius: 0,
    m: 0,
    p: 0,
  },
  '.code-block > pre:first-of-type': {
    textAlign: 'right',
    borderRight: border,
  },
  '.code-block > pre:nth-of-type(2)': {
    flex: 1,
  },
  '.code-block > pre > code': {
    p: 4,
    border: 'none',
    borderRadius: 0,
  },
  '.code-block > .highlight': {
    width: '100%',
  },
  '.code-block > .highlight > pre': {
    m: 0,
    width: '100%',
  },

  table: {
    m: 0,
  },

  'table pre': {
    m: 0,
  },

  td: {
    p: 0,
    border: 0,
  },
}
