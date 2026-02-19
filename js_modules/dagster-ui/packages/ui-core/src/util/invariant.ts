/**
 * Assert a condition is truthy, narrowing its type.
 * Throws an error with the provided message if the condition is falsy.
 *
 * @example
 * invariant(array.length > 0, 'Array must not be empty');
 * // TypeScript now knows array.length > 0
 */
export function invariant(condition: unknown, message?: string): asserts condition {
  if (!condition) {
    throw new Error(message ?? 'Invariant violation');
  }
}

/**
 * Assert a value is not null or undefined, returning the narrowed type.
 * Use this as a replacement for non-null assertions (!)
 *
 * @example
 * // Instead of: const el = document.querySelector('.foo')!;
 * const el = assertExists(document.querySelector('.foo'), 'Expected .foo element');
 */
export function assertExists<T>(value: T | null | undefined, message?: string): T {
  if (value === null || value === undefined) {
    throw new Error(message ?? 'Expected value to exist');
  }
  return value;
}
