import type { ProfilePreferences } from "./types";

export const defaultProfilePreferences: ProfilePreferences = {
  max_distance_km: 500, preferred_transport: "suburban",
  origin: "Москва", pace: "balanced", interests: ["Прогулки", "Местная кухня"],
};
export const profileInterests = ["Природа", "История", "Местная кухня", "Прогулки", "Активный отдых", "Музеи"];
