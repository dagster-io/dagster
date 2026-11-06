// Hillpointe: open any page with ?kiosk to hide the navigation, for the TV.
// Read once at load so the flag survives in-app navigation that drops the query string.
export const isKioskMode =
  typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('kiosk');
