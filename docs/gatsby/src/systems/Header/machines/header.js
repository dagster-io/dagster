import { Machine, assign } from 'xstate'

export const headerMachine = Machine(
  {
    id: 'header',
    initial: 'idle',
    states: {
      idle: {
        on: {
          SET_INITIAL_WIDTH: {
            target: 'checking',
            actions: 'setWidth',
          },
        },
      },
      checking: {
        on: {
          '': [
            {
              target: 'nothing',
              cond: ctx => {
                return ctx.width > 600
              },
            },
            { target: 'closed' },
          ],
        },
      },
      closed: {
        entry: assign({ value: '' }),
        on: {
          TOGGLE: 'opened',
        },
      },
      opened: {
        on: {
          TOGGLE: 'closed',
        },
      },
      nothing: {},
    },
    on: {
      SET_WIDTH: {
        target: 'checking',
        actions: 'setWidth',
      },
      CHANGE: {
        actions: assign({ value: (_, ev) => ev.data }),
      },
    },
  },
  {
    actions: {
      setWidth: assign({
        width: (_, ev) => ev.data,
      }),
    },
  },
)
