export const OPENERS = [
  "I think you'd like the following:",
  "These feel closest to what you described:",
  "Here's where I'd start:",
  "A few places that fit:",
  "These stood out:",
  "Start with these:",
  "This is the short list:",
  "The closest matches:",
  "Worth a look:",
  "These line up with that:",
  "I'd begin here:",
  "A few places for this:",
  "The ones I'd send you to:",
  "Closest to that feeling:",
  "Here's a first pass:",
  "These should get you close:",
  "A few that fit the mood:",
  "I'd look at these first:",
  "This is the top of the list:",
  "These feel right:",
  "The best of what I found:",
  "Start here:",
  "The ones that match:",
  "This is where I'd go:",
  "Pulled from the top of the list:",
  "The ones that fit best:",
  "Here's what I'd try:",
  "These are the ones:",
  "Somewhere to begin:",
  "This came up first:",
];

const STORAGE_KEY = 'vibio-opener';

export function nextOpener() {
  let cursor = 0;
  try {
    cursor = Number(sessionStorage.getItem(STORAGE_KEY) || 0) || 0;
  } catch {
    cursor = 0;
  }
  const line = OPENERS[cursor % OPENERS.length];
  try {
    sessionStorage.setItem(STORAGE_KEY, String(cursor + 1));
  } catch {
    // The rotation still advances for this page load.
  }
  return line;
}
