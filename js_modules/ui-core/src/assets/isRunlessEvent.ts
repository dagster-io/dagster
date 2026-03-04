// Just definining this to give an otherwise innocuous looking check a better name
export function isRunlessEvent(event: {runId: string}) {
  return event.runId === '';
}
