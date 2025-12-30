import type { MessagePort } from 'node:worker_threads';
export type AnyFn<R = any, T extends any[] = any[]> = (...args: T) => R;
export type Syncify<T extends AnyFn> = (...args: Parameters<T>) => Awaited<ReturnType<T>>;
export type ValueOf<T> = T[keyof T];
export interface MainToWorkerMessage<T extends unknown[]> {
    id: number;
    args: T;
}
export interface MainToWorkerCommandMessage {
    id: number;
    cmd: string;
}
export interface WorkerData {
    sharedBufferView: Int32Array;
    workerPort: MessagePort;
    pnpLoaderPath: string | undefined;
}
export interface DataMessage<T> {
    result?: T;
    error?: unknown;
    properties?: unknown;
}
export interface StdioChunk {
    type: 'stderr' | 'stdout';
    chunk: Uint8Array | string;
    encoding: BufferEncoding;
}
export interface WorkerToMainMessage<T> extends DataMessage<T> {
    id: number;
    stdio: StdioChunk[];
}
export interface GlobalShim {
    moduleName: string;
    globalName?: string;
    named?: string | null;
    conditional?: boolean;
}
export interface PackageJson {
    type?: 'commonjs' | 'module';
}
