// Owner credentials live only in this browser tab's memory, never in Vite assets,
// URLs, browser storage, or provider adapters. Refresh requires entering it again.
let ownerToken = "";
export function setOwnerToken(value: string) { ownerToken = value.trim(); }
export function getOwnerToken() { return ownerToken; }
