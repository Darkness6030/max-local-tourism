import cities from "../../src/assets/cities.json" with { type: "json" };
import tripData from "../../src/assets/trip-presets.json" with { type: "json" };
import moodData from "../../src/assets/mood-presets.json" with { type: "json" };
import type { Draft } from "./types.ts";
import type { TripPreset } from "./presets.ts";

const trips: (Omit<TripPreset, "pace"> & { pace: string })[] = tripData;
const moods: {
  id: string; title: string; subtitle: string; illustration: string;
  interests: string[]; pace: string; color: string; ink: string;
}[] = moodData;

function pace(value: string): Draft["pace"] {
  if (value === "relaxed" || value === "balanced" || value === "intensive") return value;
  throw new Error(`Неизвестный темп пресета: ${value}`);
}

function illustration(value: string) {
  if (value === "nature" || value === "city" || value === "coffee" || value === "route") return value;
  throw new Error(`Неизвестная иллюстрация пресета: ${value}`);
}

function uniqueIds(items: { id: string }[]) {
  const ids = new Set<string>();
  for (const item of items) {
    if (!/^[a-z][a-z0-9-]*$/.test(item.id) || ids.has(item.id)) {
      throw new Error(`Некорректный или повторяющийся id пресета: ${item.id}`);
    }
    ids.add(item.id);
  }
}

uniqueIds(trips);
uniqueIds(moods);

// Both Vite and the app load these settings: invalid catalogs fail the build.
export const configuredTrips: TripPreset[] = trips.map((trip) => {
  if (!cities.cities.some((city) => city.name === trip.origin)) {
    throw new Error(`Неизвестный город отправления пресета: ${trip.origin}`);
  }
  if (trip.days.length < 1 || trip.days.length > 3 || trip.days.some((day) => !day.stops.length)) {
    throw new Error(`Пресет ${trip.id} должен содержать программу на 1–3 дня`);
  }
  if (trip.budgetRub <= 0 || trip.budgetItems.some((item) => item.amount < 0) ||
      trip.budgetItems.reduce((sum, item) => sum + item.amount, 0) !== trip.budgetRub) {
    throw new Error(`Расходы пресета ${trip.id} должны складываться в budgetRub`);
  }
  if (!/^[a-zA-Z0-9_-]+\.(jpg|jpeg|png|webp)$/.test(trip.photo)) {
    throw new Error(`Некорректное имя фотографии пресета: ${trip.photo}`);
  }
  return { ...trip, pace: pace(trip.pace) };
});

export const moodPresets = moods.map((mood) => {
  if (!mood.title.trim() || !mood.interests.length ||
      !/^#[0-9a-f]{6}$/i.test(mood.color) || !/^#[0-9a-f]{6}$/i.test(mood.ink)) {
    throw new Error(`Проверьте название, интересы и цвета пресета ${mood.id}`);
  }
  return { ...mood, pace: pace(mood.pace), illustration: illustration(mood.illustration) };
});
export type MoodPreset = (typeof moodPresets)[number];
