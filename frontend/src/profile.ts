import type { ProfilePreferences } from "./types";

export const defaultProfilePreferences: ProfilePreferences = {
  display_name: "", avatar_style: "max", avatar_color: "lavender",
  origin: "Москва", pace: "balanced", interests: ["Прогулки", "Местная кухня"],
};
export const profileColors = {
  lavender: { name: "Лаванда", background: "#ebe8fc", color: "#6b60a8" },
  sage: { name: "Шалфей", background: "#e6efdf", color: "#627e62" },
  peach: { name: "Персик", background: "#fae8da", color: "#a97056" },
  sky: { name: "Небо", background: "#e1edf7", color: "#577e9d" },
};
export const profileInterests = ["Природа", "История", "Местная кухня", "Прогулки", "Активный отдых", "Музеи"];
