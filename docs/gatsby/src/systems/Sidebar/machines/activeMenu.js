import { Machine, assign } from 'xstate'

const machine = Machine({
  id: 'activeMenu',
  initial: 'idle',
  states: {
    idle: {
      on: {
        FIND_REFERENCE: 'finding',
      },
    },
    finding: {
      entry: ['findActive', 'saveOnLocalStorage'],
      on: {
        FIND_REFERENCE: 'finding',
      },
    },
  },
})

const activeFromPathName = (ctx, ev) => {
  const { pathname } = ev.location
  const version = pathname.match(/^\/([^/]*).*$/)[1]
  const match = pathname.replace(`${version}/`, '').match(/((\w+)-(\w+)|(\w+))/)
  return match && match[0]
}

const actions = {
  findActive: assign((ctx, ev) => {
    if (typeof window === 'undefined') return ctx

    const { pathname } = ev.location
    const id = pathname === '/' ? 'home' : activeFromPathName(ctx, ev)
    const node = document.getElementById(id)

    return {
      ...ctx,
      active: id,
      top: node ? node.offsetTop : 0,
    }
  }),
  saveOnLocalStorage: ctx => {
    if (typeof window === 'undefined') return ctx
    ctx.top !== 0 && ctx.storage.set(ctx.top)
  },
}

export const activeMenuMachine = machine.withConfig({
  actions,
})
