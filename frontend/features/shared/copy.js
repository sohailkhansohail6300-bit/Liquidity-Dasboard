/* Same behaviour as App.copy(): clipboard when available, otherwise a prompt to copy by hand. */
export function copyText(text, toast) {
  const done = () => toast('Link copied');
  if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, () => window.prompt('Copy this link', text));
  } else window.prompt('Copy this link', text);
}
