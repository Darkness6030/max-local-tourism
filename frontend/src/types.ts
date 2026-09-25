export interface Identity {
  mode: "max" | "local";
  user: {
    id: number;
    first_name: string;
    last_name?: string | null;
    username?: string | null;
    photo_url?: string | null;
  };
}
export interface AppConfig {
  bot_url?: string | null;
  today: string;
  default_date: string;
  last_trip_date: string;
  max_days: number;
  origins: string[];
}
export interface TripRequest {
  origin: string;
  destination: string | null;
  start_date: string;
  days: number;
  budget_rub: number;
  travelers: number;
  group_type: "solo" | "couple" | "friends" | "family";
  children_ages: number[];
  preferences: string;
  pace: "relaxed" | "balanced" | "intensive";
  has_car: boolean;
  departure_after: string;
  return_after: string;
  max_travel_minutes: number;
}
export interface Draft extends TripRequest {
  interests: string[];
  childrenText: string;
  destinationMode: "ai" | "manual";
}
export interface TimelineItem {
  start_time: string;
  end_time: string;
  title: string;
  place: string;
  description: string;
  indoor: boolean;
  estimated_cost_rub: number;
}
export interface TransportOption {
  departure: string;
  arrival: string;
  duration_minutes: number;
  from_station: string;
  to_station: string;
  price_rub: number | null;
  buy_url: string;
  map_url: string | null;
  transport_type: string;
  has_transfers: boolean;
}
export interface Accommodation {
  check_in: string;
  check_out: string;
  nights: number;
  rooms: number;
  estimated_room_night_rub: number;
  estimated_total_rub: number;
  status: "found" | "empty" | "unavailable";
  hotels: {
    id: string;
    name: string;
    kind: "hotel" | "guest_house";
    address: string | null;
    distance_km: number;
    website: string | null;
    map_url: string;
    source_url: string;
  }[];
  search_url: string;
  fetched_at: string | null;
  disclaimer: string;
}
export interface TripPlan {
  id: string;
  title: string;
  summary: string;
  request: TripRequest;
  created_at: string;
  origin: { title: string };
  destination: { title: string };
  accommodation?: Accommodation | null;
  destination_reason?: string | null;
  destination_photo?: {
    url: string;
    source_url: string;
    article_url: string;
    author: string;
    license: string;
  } | null;
  itinerary: { date: string; title: string; items: TimelineItem[] }[];
  budget: {
    limit_rub: number;
    estimated_total_rub: number;
    per_person_rub: number;
    within_budget: boolean;
    items: { category: string; amount_rub: number; comment?: string | null }[];
    disclaimer: string;
  };
  weather: {
    provider: string;
    days: {
      date: string;
      description: string;
      temperature_min_c: number;
      temperature_max_c: number;
      precipitation_probability_percent?: number | null;
    }[];
  };
  transport: {
    outbound: TransportOption[];
    return_trip: TransportOption[];
    source_name: string;
  } | null;
  weather_advice: string;
  packing_list: string[];
  packed_items: number[];
  warnings: string[];
  notes: string[];
  sources: { name: string; url: string }[];
  share_text: string;
  map_url: string | null;
}
export interface Job {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  progress: number;
  message: string;
  events: { progress: number; message: string }[];
  result: TripPlan | null;
  error: { error: string } | null;
}
export type Screen =
  "home" | "wizard" | "loading" | "result" | "preset" | "trips" | "about";
export interface Bridge {
  initData?: string;
  ready?: () => void;
  enableClosingConfirmation?: () => void;
  disableClosingConfirmation?: () => void;
  shareMaxContent?: (data: { text: string }) => Promise<unknown> | void;
  openLink?: (url: string) => Promise<unknown> | void;
  BackButton?: {
    show?: () => void;
    hide?: () => void;
    onClick?: (callback: () => void) => void;
    offClick?: (callback: () => void) => void;
  };
}
declare global {
  interface Window {
    WebApp?: Bridge;
  }
}
