/**
 * Helpers for run notification email validation and subscription flow.
 */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  return EMAIL_REGEX.test(trimmed);
}

export type ValidateSubscriptionEmailResult =
  | {valid: true; error: null}
  | {valid: false; error: string};

export function validateSubscriptionEmail(
  email: string,
  existingEmails: string[],
): ValidateSubscriptionEmailResult {
  const trimmed = email.trim();
  if (!trimmed) {
    return {valid: false, error: 'Enter an email address'};
  }
  if (!isValidEmail(trimmed)) {
    return {valid: false, error: 'Enter a valid email address (e.g. name@example.com)'};
  }
  if (existingEmails.includes(trimmed)) {
    return {valid: false, error: 'This email is already subscribed'};
  }
  return {valid: true, error: null};
}
