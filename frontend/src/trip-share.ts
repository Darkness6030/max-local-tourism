/** Open exactly one share menu in the user's click stack, using the prepared text. */
export function shareTrip(text: string, initData: string): void {
  const bridge = window.WebApp;
  const inMax = Boolean(initData || bridge?.initData);
  const deepLink = `https://max.ru/:share?text=${encodeURIComponent(text)}`;
  try {
    const result = inMax && bridge?.platform === "ios" && bridge.openMaxLink
      ? bridge.openMaxLink(deepLink)
      : inMax && bridge?.shareMaxContent ? bridge.shareMaxContent({ text })
      : inMax && bridge?.openMaxLink ? bridge.openMaxLink(deepLink)
      : inMax && (bridge?.platform === "ios" || bridge?.platform === "android") && bridge.shareContent
        ? bridge.shareContent({ text })
      : navigator.share?.({ text });
    // Sharing is intentionally silent: no diagnostic popup or second native menu.
    // Copy remains available if the client rejects or the user cancels sharing.
    Promise.resolve(result).catch(() => {});
  } catch {
    // Some clients throw synchronously instead of rejecting the request.
  }
}
