import type { AppConfig, Draft, TripRequest } from "./types";

export const money = (value: number) =>
  `${new Intl.NumberFormat("ru-RU").format(value)} ₽`;
const nightRules = new Intl.PluralRules("ru-RU");
export const nightsLabel = (count: number) => {
  const form = nightRules.select(count);
  return `${count} ${form === "one" ? "ночь" : form === "few" ? "ночи" : "ночей"}`;
};
export const dateLabel = (
  value: string,
  options?: Intl.DateTimeFormatOptions,
) =>
  value && Number.isFinite(Date.parse(value))
    ? new Date(`${value}T12:00:00`).toLocaleDateString(
        "ru-RU",
        options || { day: "numeric", month: "long" },
      )
    : "Выберите дату";
export const timeLabel = (value: string) =>
  new Date(value).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Moscow",
  });
export const addDays = (value: string, days: number) => {
  const date = new Date(`${value}T12:00:00Z`);
  if (!Number.isFinite(date.getTime())) return "";
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
};
export class ApiError extends Error {
  constructor(
    message: string,
    public status = 0,
  ) {
    super(message);
  }
}

// Also normalize prose in restored plans and provider responses. Keep request
// values, profile data, identifiers and links exactly as received.
const displayFields = new Set([
  "title",
  "summary",
  "description",
  "comment",
  "weather_advice",
  "destination_reason",
  "warnings",
  "notes",
  "packing_list",
  "share_text",
  "text",
  "message",
  "error",
  "detail",
  "msg",
  "name",
]);
function localizeDisplayText<T>(value: T, field = ""): T {
  if (field === "request" || field === "user") return value;
  if (typeof value === "string" && displayFields.has(field)) {
    return value
      .split(/(https?:\/\/\S+)/g)
      .map((part) =>
        /^https?:\/\//.test(part)
          ? part
          : part.replace(/\b(?:AI|GigaChat)\b/g, "ИИ"),
      )
      .join("") as T;
  }
  if (Array.isArray(value))
    return value.map((item) => localizeDisplayText(item, field)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        localizeDisplayText(item, key),
      ]),
    ) as T;
  }
  return value;
}
export async function api<T>(
  path: string,
  initData: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const onAbort = () => controller.abort();
  options.signal?.addEventListener("abort", onAbort, { once: true });
  if (options.signal?.aborted) controller.abort();
  const timeout = setTimeout(() => controller.abort(), 20_000);
  try {
    const response = await fetch(
      `${import.meta.env.BASE_URL.replace(/\/static\/$/, "").replace(/\/$/, "")}/api/v1${path}`,
      {
        ...options,
        signal: controller.signal,
        cache: "no-store",
        headers: {
          ...(options.body ? { "Content-Type": "application/json" } : {}),
          ...(initData ? { "X-Max-Init-Data": initData } : {}),
        },
      },
    );
    const data = localizeDisplayText(await response.json());
    if (!response.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail
            .map((entry: { msg: string }) =>
              entry.msg.replace(/^Value error, /, ""),
            )
            .join(". ")
        : data.error || data.detail;
      throw new ApiError(
        detail || "Не удалось выполнить запрос. Попробуйте ещё раз.",
        response.status,
      );
    }
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (options.signal?.aborted) throw error;
    throw new ApiError(
      "Сервер не ответил. Проверьте соединение и попробуйте ещё раз.",
    );
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", onAbort);
  }
}
export function readStorage<T>(
  key: string,
  fallback: T,
  persistent = false,
): T {
  try {
    return (
      JSON.parse(
        (persistent ? localStorage : sessionStorage).getItem(key) || "null",
      ) ?? fallback
    );
  } catch {
    return fallback;
  }
}
export function writeStorage(key: string, value: unknown, persistent = false) {
  try {
    const storage = persistent ? localStorage : sessionStorage;
    if (value === null) storage.removeItem(key);
    else storage.setItem(key, JSON.stringify(value));
  } catch {
    /* Storage is optional in restricted WebViews. */
  }
}
export function initialDraft(config: AppConfig): Draft {
  return {
    origin: "Москва",
    destination: null,
    destinationMode: "ai",
    start_date: config.default_date,
    days: 1,
    budget_rub: 12000,
    travelers: 2,
    group_type: "couple",
    children_ages: [],
    childrenText: "",
    preferences: "",
    interests: ["Прогулки", "Местная кухня"],
    pace: "balanced",
    has_car: false,
    departure_after: "08:00",
    return_after: "18:00",
    max_travel_minutes: 240,
  };
}
export function restoreDraft(
  raw: Partial<Draft> | null,
  config: AppConfig,
): Draft {
  const base = initialDraft(config);
  if (!raw || typeof raw !== "object") return base;
  const draft = { ...base, ...raw };
  if (!config.origins.includes(draft.origin)) draft.origin = base.origin;
  if (
    !Number.isInteger(draft.days) ||
    draft.days < 1 ||
    draft.days > config.max_days
  )
    draft.days = 1;
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(draft.start_date) ||
    draft.start_date < config.today ||
    draft.start_date > addDays(config.last_trip_date, 1 - draft.days)
  )
    draft.start_date = config.default_date;
  if (!Array.isArray(draft.interests)) draft.interests = base.interests;
  return draft;
}
export function validateStep(
  step: number,
  draft: Draft,
  config: AppConfig,
): string | null {
  if (
    step === 0 &&
    draft.destinationMode === "manual" &&
    (!draft.destination || draft.destination.trim().length < 2)
  )
    return "Введите город назначения — минимум две буквы.";
  if (
    step === 1 &&
    (!draft.start_date ||
      draft.start_date < config.today ||
      addDays(draft.start_date, draft.days - 1) > config.last_trip_date)
  )
    return "Выберите даты в пределах доступного прогноза.";
  if (step === 2) {
    if (
      !Number.isInteger(draft.travelers) ||
      draft.travelers < 1 ||
      draft.travelers > 20
    )
      return "В поездке может быть от 1 до 20 человек.";
    if (draft.group_type === "family" && draft.childrenText.trim()) {
      if (!/^\d{1,2}(\s*,\s*\d{1,2})*$/.test(draft.childrenText.trim()))
        return "Введите возраст детей через запятую: например, 5, 12.";
      const ages = draft.childrenText.split(",").map(Number);
      if (ages.some((age) => age > 17) || ages.length > 10)
        return "Укажите возраст от 0 до 17 лет, не более 10 детей.";
      if (ages.length >= draft.travelers)
        return "Добавьте хотя бы одного взрослого к числу путешественников.";
    }
  }
  if (
    step === 3 &&
    !draft.interests.length &&
    draft.preferences.trim().length < 3
  )
    return "Выберите хотя бы один интерес или расскажите о пожеланиях.";
  if (step === 4) {
    if (
      !Number.isInteger(draft.budget_rub) ||
      draft.budget_rub < 1000 ||
      draft.budget_rub > 1000000
    )
      return "Укажите общий бюджет от 1 000 до 1 000 000 ₽.";
    if (!draft.departure_after || !draft.return_after)
      return "Укажите удобное время выезда и возвращения.";
  }
  return null;
}
export function toRequest(draft: Draft): TripRequest {
  const { interests, childrenText, destinationMode, ...request } = draft;
  return {
    ...request,
    destination:
      destinationMode === "manual" ? draft.destination?.trim() || null : null,
    children_ages:
      draft.group_type === "family" && childrenText.trim()
        ? childrenText.split(",").map(Number)
        : [],
    preferences: [...interests, draft.preferences.trim()]
      .filter(Boolean)
      .join("; ")
      .slice(0, 1500),
  };
}
export function safeUrl(value: string | null): string | undefined {
  try {
    const url = new URL(value || "");
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
export function openExternal(url: string) {
  const safe = safeUrl(url);
  if (!safe) return;
  if (window.WebApp?.initData && window.WebApp.openLink)
    return window.WebApp.openLink(safe);
  window.open(safe, "_blank", "noopener,noreferrer");
}
