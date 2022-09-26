// https://developer.chrome.com/blog/how-to-convert-arraybuffer-to-and-from-string/

export function arrayBufferToString(buf: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint16Array(buf);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    const char = String.fromCharCode(bytes[i]);
    if (char !== '\x00') {
      binary += char;
    }
  }
  return binary;
}

export function stringToArrayBuffer(str: string): ArrayBuffer {
  const buf = new ArrayBuffer(str.length * 2); // 2 bytes for each char
  const bufView = new Uint16Array(buf);
  for (let i = 0, strLen = str.length; i < strLen; i++) {
    if (str[i] !== '\x00') {
      bufView[i] = str.charCodeAt(i);
    }
  }
  return buf;
}
