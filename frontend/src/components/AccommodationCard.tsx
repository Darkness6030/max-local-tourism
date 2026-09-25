import { ArrowUpRight, BedDouble, MapPin } from "lucide-react";
import type { Accommodation } from "../types";
import { dateLabel, money, safeUrl } from "../lib";

const linkStyles =
  "inline-flex min-h-[44px] items-center gap-[5px] text-[12px] font-semibold text-brand no-underline";

export function AccommodationCard({
  stay,
  external,
}: {
  stay: Accommodation;
  external: (url: string) => void;
}) {
  return (
    <section
      data-ui="accommodation-card"
      className="mt-[24px] rounded-[20px] border border-solid border-[var(--line)] bg-white p-[22px] mobile:mt-[16px] mobile:rounded-[18px] mobile:p-[19px]"
    >
      <div className="flex items-center gap-[12px]">
        <span className="grid h-[39px] w-[39px] shrink-0 place-items-center rounded-[13px] bg-[#ecf0ff] text-brand">
          <BedDouble size={22} />
        </span>
        <div>
          <h2 className="text-[14px] font-bold">Где остановиться</h2>
          <p className="mt-[5px] text-[11px] leading-[1.7] text-muted">
            {dateLabel(stay.check_in)} — {dateLabel(stay.check_out)} ·{" "}
            {stay.nights} ноч.
          </p>
        </div>
      </div>
      <div className="mt-[18px] rounded-[13px] bg-[#f5f7fb] px-[14px] py-[12px] text-[12px] leading-[1.8]">
        <p>
          Ориентир: <strong>≈ {money(stay.estimated_room_night_rub)}</strong> за
          номер / ночь
        </p>
        <p className="mt-[3px] text-muted">
          {stay.rooms} ном. × {stay.nights} ноч. · ≈{" "}
          {money(stay.estimated_total_rub)} за поездку
        </p>
        <p className="mt-[3px] text-[11px] text-muted">
          Учтено в бюджете; запас указан отдельно. До 2 гостей в номере,
          размещение детей уточняйте.
        </p>
      </div>
      <p className="mt-[12px] text-[11px] leading-[1.8] text-muted">
        {stay.disclaimer}
      </p>
      <div className="mt-[8px] divide-x-0 divide-y divide-solid divide-[var(--line)]">
        {stay.hotels.map((hotel) => (
          <article
            key={hotel.id}
            data-ui="hotel-card"
            className="py-[14px] first:pt-[10px]"
          >
            <h3 className="text-[13px] font-bold leading-[1.6] [overflow-wrap:anywhere]">
              {hotel.name}
            </h3>
            <p className="mt-[3px] text-[11px] leading-[1.8] text-muted">
              {hotel.kind === "hotel" ? "Гостиница" : "Гостевой дом"} ·{" "}
              {hotel.distance_km.toLocaleString("ru-RU")} км от центра по прямой
            </p>
            {hotel.address && (
              <p className="mt-[4px] text-[12px] leading-[1.7] text-[#687389] [overflow-wrap:anywhere]">
                {hotel.address}
              </p>
            )}
            <div className="mt-[4px] flex flex-wrap items-center gap-x-[18px]">
              <a
                className={linkStyles}
                href={safeUrl(hotel.map_url)}
                target="_blank"
                rel="noreferrer"
                onClick={(event) => {
                  event.preventDefault();
                  external(hotel.map_url);
                }}
              >
                <MapPin size={14} /> На карте
              </a>
              {hotel.website && safeUrl(hotel.website) && (
                <a
                  className={linkStyles}
                  href={safeUrl(hotel.website)}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(event) => {
                    event.preventDefault();
                    external(hotel.website!);
                  }}
                >
                  Сайт гостиницы <ArrowUpRight size={14} />
                </a>
              )}
            </div>
          </article>
        ))}
      </div>
      {!stay.hotels.length && (
        <p
          data-ui="hotel-empty"
          className="mt-[14px] text-[12px] leading-[1.8] text-[#687389]"
        >
          {stay.status === "empty"
            ? "В каталоге пока нет гостиниц рядом с центром города."
            : "Сейчас не удалось загрузить гостиницы. Посмотрите варианты на карте."}
        </p>
      )}
      <a
        className={linkStyles}
        href={safeUrl(stay.search_url)}
        target="_blank"
        rel="noreferrer"
        onClick={(event) => {
          event.preventDefault();
          external(stay.search_url);
        }}
      >
        Все гостиницы на карте <ArrowUpRight size={14} />
      </a>
      <p className="mt-[5px] text-[10px] leading-[1.8] text-muted">
        <a
          className="text-inherit"
          href="https://www.openstreetmap.org/copyright"
          target="_blank"
          rel="noreferrer"
        >
          © OpenStreetMap contributors · ODbL
        </a>
        {stay.fetched_at && ` · ${dateLabel(stay.fetched_at.slice(0, 10))}`}
      </p>
    </section>
  );
}
