import type { Draft } from "./types";
import { configuredTrips } from "./preset-config";

export interface TripPreset {
  id: string;
  city: string;
  origin: string;
  title: string;
  tagline: string;
  summary: string;
  photo: string;
  photoAlt: string;
  photoAuthor: string;
  photoSource: string;
  interests: string[];
  pace: Draft["pace"];
  maxTravelMinutes: number;
  budgetRub: number;
  budgetItems: { label: string; amount: number }[];
  travel: string;
  tip: string;
  packing: string[];
  sources: { name: string; url: string }[];
  days: {
    title: string;
    stops: {
      time: string;
      title: string;
      place: string;
      description: string;
    }[];
  }[];
}

const photos = import.meta.glob<string>("./assets/presets/*.{jpg,jpeg,png,webp}", {
  eager: true, query: "?url", import: "default",
});

export const tripPresets: TripPreset[] = configuredTrips.map((preset) => {
  const photo = photos[`./assets/presets/${preset.photo}`];
  if (!photo) throw new Error(`Нет фотографии для пресета ${preset.id}: ${preset.photo}`);
  return { ...preset, photo };
});
