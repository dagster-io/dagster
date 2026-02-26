export function testId(id: string): string | null {
  if (process.env.NODE_ENV === 'test' || typeof jest !== 'undefined') {
    return id;
  }
  return null;
}
