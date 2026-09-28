import type { AppConfig } from "./types";
import fallbackHero from "./assets/journey.webp";

// New local covers only need a file in assets/ and its filename in cities.json.
const covers = import.meta.glob<string>("./assets/*.{webp,png,jpg,jpeg}", {
  eager: true,
  query: "?url",
  import: "default",
});

export const cityDetails = (config: AppConfig, origin: string) =>
  config.origin_details?.find((city) => city.name === origin);

export const cityHero = (config: AppConfig, origin: string) =>
  covers[`./assets/${cityDetails(config, origin)?.hero_image}`] || fallbackHero;
