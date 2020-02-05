import { Machine, assign } from 'xstate'

const machine = Machine({
  id: 'responsive',
  initial: 'idle',
  states: {
    idle: {
      on: {
        SET_INITIAL_WIDTH: {
          actions: ['setWidth'],
          target: 'checking',
        },
      },
    },
    checking: {
      on: {
        '': [{ target: 'showing', cond: 'isDesktop' }, { target: 'closed' }],
      },
    },
    closed: {
      on: {
        MENU_CLICK: 'showing',
        TOGGLE: 'showing',
      },
    },
    showing: {
      on: {
        TOGGLE: 'closed',
      },
    },
  },
  on: {
    SET_WIDTH: {
      actions: ['setWidth'],
      target: 'checking',
    },
  },
})

const guards = {
  isDesktop: ctx => {
    return ctx.width >= 1366
  },
}

const actions = {
  setWidth: assign({
    width: (_, ev) => ev.data,
  }),
}

export const responsiveMachine = machine.withConfig({
  guards,
  actions,
})
