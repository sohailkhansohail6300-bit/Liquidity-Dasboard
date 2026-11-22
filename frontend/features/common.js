/* Shared by several pages: copy a link to the clipboard (same behaviour as App.copy in the prototype). */
export function copyText(text, toast) {
  const done = () => toast('Link copied');
  if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, () => { window.prompt('Copy this link', text); });
  } else {
    window.prompt('Copy this link', text);
  }
}

/* Move focus to the first invalid control inside `root` (used after a failed submit). */
export function focusFirstInvalid(root) {
  setTimeout(() => {
    const el = root && root.querySelector ? root.querySelector('[aria-invalid]') : null;
    if (el) el.focus();
  }, 0);
}
