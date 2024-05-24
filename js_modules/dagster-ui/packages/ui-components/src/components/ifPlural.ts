export function ifPlural(
  count: number | undefined | null,
  singularString: string,
  pluralString: string,
) {
  return count === 1 ? singularString : pluralString;
}
