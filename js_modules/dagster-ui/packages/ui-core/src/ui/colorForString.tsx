import memoize from 'lodash/memoize';

// For a given list of colors, deterministically return a color string
// for a supplied input string.
export const colorForString = (colors: string[]) =>
  memoize((s: string) => {
    const index =
      Math.abs(
        s.split('').reduce((a, b) => {
          a = (a << 5) - a + b.charCodeAt(0);
          return a & a;
        }, 0),
      ) % colors.length;
    return colors[index]!;
  });
