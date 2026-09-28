import type { AppConfig, ProfilePreferences } from "./types";

export const defaultProfilePreferences = (config: AppConfig): ProfilePreferences => ({
  max_distance_km: 500, preferred_transport: "suburban",
  origin: config.default_origin || config.origins[0], pace: "balanced", interests: ["Прогулки", "Местная кухня"],
});
export const profileInterests = ["Природа", "История", "Местная кухня", "Прогулки", "Активный отдых", "Музеи"];
