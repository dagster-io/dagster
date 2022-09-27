// https://developer.chrome.com/blog/how-to-convert-arraybuffer-to-and-from-string/

export function arrayBufferToString(buf: ArrayBuffer): string {
  return String.fromCharCode.apply(null, new Uint16Array(buf) as any);
}

// Chunk the data into 16kb bytes to avoid hitting max argument errors when converting back to a string
// with String.fromCharCode.apply
const MAX_BUFFER_SIZE = 16000;
export function stringToArrayBuffers(str: string): ArrayBuffer[] {
  const buffers: ArrayBuffer[] = [];
  let buf = new ArrayBuffer(0);
  let view = new Uint16Array(buf);
  for (let i = 0, strLen = str.length; i < strLen; i++) {
    const index = i % MAX_BUFFER_SIZE;
    if (index === 0) {
      buf = new ArrayBuffer(Math.min(MAX_BUFFER_SIZE, str.length - i) * 2); // 2 bytes for each char\
      view = new Uint16Array(buf);
      buffers.push(buf);
    }
    view[index] = str.charCodeAt(i);
  }
  return buffers;
}
