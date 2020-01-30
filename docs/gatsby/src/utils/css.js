import * as R from 'ramda'

export const theme = str => R.path(str.split('.'))
export const rem = val => `${val / 18}rem`
