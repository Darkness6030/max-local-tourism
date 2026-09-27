import { useEffect, useRef, useState } from "react";

export type ShareMethod = "deeplink" | "link" | "text-link" | "text" | "full" | "native" | "browser";
export const shareLabels: Record<ShareMethod, string> = {
  deeplink: "MAX: диплинк",
  link: "MAX: ссылка",
  "text-link": "MAX: текст + ссылка",
  text: "MAX: короткий текст",
  full: "MAX: полный план",
  native: "Системное меню MAX",
  browser: "Другой способ",
};

// Temporary, local-only diagnostics. Never serialize Bridge, initData or the payload.
function errorDetails(error: unknown, privateValues: string[]): string {
  const outer: Record<string, unknown> = typeof error === "string"
    ? { message: error } : error && typeof error === "object" ? error as Record<string, unknown> : {};
  const inner = outer.error && typeof outer.error === "object"
    ? outer.error as Record<string, unknown> : outer;
  const parts = [inner.code, inner.name, inner.message, outer.name,
    typeof outer.error === "string" ? outer.error : undefined]
    .filter((value): value is string => typeof value === "string");
  let value = [...new Set(parts)].join(" · ") || "Ошибка без кода";
  for (const secret of privateValues.filter(Boolean)) {
    value = value.split(secret).join("[скрыто]");
    value = value.split(encodeURIComponent(secret)).join("[скрыто]");
  }
  return value.replace(/https?:\S+|trip_[\w-]+|[\w%=-]{32,}/g, "[скрыто]").slice(0, 240);
}

export function useTripShare(text: string, url: string, initData: string) {
  const [open, setOpen] = useState(false);
  const [logs, setLogs] = useState<{ id: number; method: ShareMethod; status: string }[]>([]);
  const counter = useRef(0);
  const timers = useRef(new Set<ReturnType<typeof setTimeout>>());
  const generation = useRef(0);
  useEffect(() => {
    setLogs([]);
    setOpen(false);
    generation.current += 1;
    const pending = timers.current;
    return () => {
      generation.current += 1;
      pending.forEach(clearTimeout);
      pending.clear();
    };
  }, [text, url, initData]);

  const bridge = window.WebApp;
  const inMax = Boolean(initData || bridge?.initData);
  const methods: ShareMethod[] = [];
  const hasDeepLink = inMax && typeof bridge?.openMaxLink === "function";
  // The documented :share deep link opens the MAX recipient picker on iOS.
  if (hasDeepLink && bridge?.platform === "ios") methods.push("deeplink");
  if (inMax && typeof bridge?.shareMaxContent === "function") {
    if (bridge?.platform !== "ios") methods.push("full");
    if (url) methods.push("link", "text-link", "text");
    if (!methods.includes("full")) methods.push("full");
  }
  if (hasDeepLink && !methods.includes("deeplink")) methods.push("deeplink");
  if (inMax && (bridge?.platform === "ios" || bridge?.platform === "android")
    && typeof bridge?.shareContent === "function") methods.push("native");
  if (typeof navigator.share === "function") methods.push("browser");

  const share = (preferred?: ShareMethod) => {
    const method = preferred ?? methods[0];
    setOpen(true);
    if (!method || !methods.includes(method) || !text) return;
    const id = ++counter.current;
    const currentGeneration = generation.current;
    const started = performance.now();
    const active = navigator.userActivation?.isActive;
    const prefix = `#${id} · клик ${active === undefined ? "?" : active ? "да" : "нет"}`;
    setLogs((values) => [...values.slice(-11), { id, method, status: `${prefix} · ожидание ответа` }]);
    const update = (status: string) => {
      if (generation.current !== currentGeneration) return;
      setLogs((values) => values.map((entry) => entry.id === id
        ? { ...entry, status: `${prefix} · ${Math.round(performance.now() - started)} мс · ${status}` } : entry));
    };
    const timer = setTimeout(() => {
      timers.current.delete(timer);
      update("нет ответа 8 с; можно проверить другой вариант");
    }, 8000);
    timers.current.add(timer);
    const done = (status: string) => {
      clearTimeout(timer);
      timers.current.delete(timer);
      update(status);
    };
    const failed = (error: unknown) => done(errorDetails(error, [initData, bridge?.initData ?? "", text, url]));
    const invitation = "Поехали со мной!";
    const shortText = url ? `${invitation}\n${url}` : text;
    try {
      // Keep every call in the click stack. Never chain native menus after a promise.
      const result = method === "deeplink"
        ? bridge!.openMaxLink!(`https://max.ru/:share?text=${encodeURIComponent(shortText)}`)
        : method === "link" ? bridge!.shareMaxContent!({ link: url })
        : method === "text-link" ? bridge!.shareMaxContent!({ text: invitation, link: url })
        : method === "text" ? bridge!.shareMaxContent!({ text: shortText })
        : method === "full" ? bridge!.shareMaxContent!({ text })
        : method === "native" ? bridge!.shareContent!({ text })
        : navigator.share({ text });
      if (result === undefined) {
        done("вызов передан; SDK не подтверждает открытие");
      } else {
        Promise.resolve(result).then((response) => {
          if (response && typeof response === "object" && "error" in response && response.error) failed(response);
          else done("SDK завершил вызов без ошибки");
        }, failed);
      }
    } catch (error) {
      failed(error);
    }
  };
  return { share, methods, logs, open, close: () => setOpen(false) };
}
