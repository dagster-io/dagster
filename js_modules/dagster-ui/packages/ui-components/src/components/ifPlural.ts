export function ifPlural(count: number | undefined | null, string: string) {
  return count === 1 ? '' : string;
}
