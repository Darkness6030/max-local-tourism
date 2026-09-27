import { useLayoutEffect } from "react";

// A software keyboard can shrink the visual viewport without resizing the page.
// Let the browser do its normal focus scroll, then reveal only the obscured part.
export function useMobileViewport() {
  useLayoutEffect(() => {
    const viewport = window.visualViewport;
    const root = document.documentElement;
    root.toggleAttribute("data-max-ios", window.WebApp?.platform === "ios");
    let frame = 0;
    let settled = 0;
    let fullHeight = window.innerHeight;

    const update = () => {
      const active = document.activeElement;
      const editing = active instanceof HTMLElement
        && active.matches("input:not([type=checkbox]):not([type=radio]), textarea, select");
      const height = viewport?.height ?? window.innerHeight;
      const top = viewport?.offsetTop ?? 0;
      const zoomed = viewport && Math.abs(viewport.scale - 1) > 0.05;
      const keyboard = editing && !zoomed && fullHeight - height > 120;
      root.toggleAttribute("data-keyboard-open", keyboard);
      root.style.setProperty("--keyboard-inset", keyboard
        ? `${Math.max(0, root.clientHeight - height - top)}px` : "0px");
      if (!editing) {
        fullHeight = window.innerHeight;
        return;
      }
      // Never compensate for a deliberate pinch zoom.
      if (zoomed) return;
      if (!window.matchMedia("(max-width: 700px), (pointer: coarse)").matches) return;
      let bottom = top + height;
      const actions = document.querySelector<HTMLElement>("[data-ui~=wizard-actions]");
      if (actions && getComputedStyle(actions).position === "sticky") {
        const rect = actions.getBoundingClientRect();
        if (rect.top > top && rect.top < bottom) bottom = rect.top;
      }
      const field = active.getBoundingClientRect();
      const space = bottom - top - 24;
      const delta = field.top < top + 12 || field.height > space
        ? field.top - top - 12
        : Math.max(0, field.bottom - bottom + 12);
      if (Math.abs(delta) > 1) window.scrollBy({ top: delta, behavior: "instant" });
    };
    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(update);
    };
    const focusChanged = () => {
      schedule();
      // Also handle WebViews that deliver the keyboard resize late.
      window.clearTimeout(settled);
      settled = window.setTimeout(schedule, 350);
    };
    document.addEventListener("focusin", focusChanged);
    document.addEventListener("focusout", focusChanged);
    window.addEventListener("resize", schedule);
    viewport?.addEventListener("resize", schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(settled);
      document.removeEventListener("focusin", focusChanged);
      document.removeEventListener("focusout", focusChanged);
      window.removeEventListener("resize", schedule);
      viewport?.removeEventListener("resize", schedule);
      root.removeAttribute("data-keyboard-open");
      root.removeAttribute("data-max-ios");
      root.style.removeProperty("--keyboard-inset");
    };
  }, []);
}
