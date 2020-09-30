import {print} from 'graphql/language/printer';
import {debounce} from 'lodash';

import {DagsterGraphQLError, showGraphQLError} from 'src/AppError';
import {WEBSOCKET_URI} from 'src/DomUtils';

type FlushCallback<T> = (messages: T[], isFirstResponse: boolean) => void;
type ErrorCallback = (error: DagsterGraphQLError) => void;

/* DirectGraphQLSubscription opens a WebSocket and sends a single GraphQL subscription
query to the Dagit process. When messages are received, it queues / debounces updates
and calls onFlushMessages. Using this class is significantly faster than Apollo for
scenarios whre a large number of messages / objects are received.

If the connection is broken, the client will attempt to re-open a new socket every 500ms.
When the connection is re-opened, the initial subscription query + variables are re-sent, and
the next call to onFlushMessages has `isFirstResponse: true`. (This implementation is not
cursor-aware and does not pick up where it left off - you should use `isFirstResponse` to
reset state in preparation for receiving messages again.)
*/
export class DirectGraphQLSubscription<T> {
  private websocket: WebSocket;
  private messageQueue: T[] = [];
  private messagesReceived = false;
  private onFlushMessages: FlushCallback<T>;
  private onError: ErrorCallback;
  private closed = false;
  private query: any;
  private variables: any;

  constructor(
    query: any,
    variables: any,
    onFlushMessages: FlushCallback<T>,
    onError: ErrorCallback,
  ) {
    this.onFlushMessages = onFlushMessages;
    this.onError = onError;
    this.query = query;
    this.variables = variables;
    this.open();
  }

  open() {
    const ws = new WebSocket(WEBSOCKET_URI);
    ws.addEventListener('message', (e) => {
      this.handleEvent(JSON.parse(e.data));
    });
    ws.addEventListener('error', this.handleRetry);
    ws.addEventListener('close', this.handleRetry);
    ws.addEventListener('open', () => {
      ws.send(JSON.stringify({type: 'connection_init', payload: {}}));
      ws.send(
        JSON.stringify({
          id: '1',
          type: 'start',
          payload: {
            extensions: {},
            variables: this.variables,
            query: print(this.query),
          },
        }),
      );
    });

    window.addEventListener('beforeunload', this.handleBeforeUnload);
    this.messagesReceived = false;
    this.websocket = ws;
    this.closed = false;
  }

  close() {
    this.closed = true;
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    this.websocket.close();
  }

  handleBeforeUnload = () => {
    this.close();
  };

  handleRetry = () => {
    setTimeout(() => {
      if (this.closed || this.websocket.readyState !== WebSocket.CLOSED) {
        return;
      }
      this.websocket.close();
      this.open();
    }, 500);
  };

  handleEvent = (msg: any) => {
    if (msg.type === 'data') {
      if (msg.payload.errors) {
        const errors = msg.payload.errors as DagsterGraphQLError[];
        errors.forEach((error) => showGraphQLError(error));
        this.onError(errors[0]);
        return;
      }
      this.messageQueue.push(msg.payload.data as T);
      this.flushUpdates();
    }
  };

  flushUpdates = debounce(() => {
    if (this.closed) {
      return;
    }
    this.onFlushMessages(this.messageQueue, !this.messagesReceived);
    this.messagesReceived = true;
    this.messageQueue = [];
  }, 50);
}
