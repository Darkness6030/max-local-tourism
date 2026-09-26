import { ACCOMMODATION_DISCLAIMER } from "../trip-copy";
import { ArrowUpRight, BedDouble, MapPin } from "lucide-react";
import type { Accommodation } from "../types";
import { dateLabel, money, nightsLabel, safeUrl } from "../lib";

const linkStyles =
  "inline-flex items-center gap-[5px] text-[12px] font-semibold text-brand no-underline";

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
      className="mt-6 rounded-[20px] border border-solid border-[var(--line)] bg-white p-5.5 mobile:mt-4
        mobile:rounded-[18px] mobile:p-[19px]"
    >
      <div className="flex items-center gap-3">
        <span className="grid h-[39px] w-[39px] shrink-0 place-items-center rounded-[13px] bg-[#ecf0ff] text-brand">
          <BedDouble size={22} />
        </span>
        <div>
          <h2 className="text-[14px] font-bold">Где остановиться</h2>
          <p className="mt-[5px] text-[11px] leading-[1.7] text-muted">
            {dateLabel(stay.check_in)} — {dateLabel(stay.check_out)} ·{" "}
            {nightsLabel(stay.nights)}
          </p>
        </div>
      </div>
      <div className="mt-4.5 rounded-[13px] bg-[#f5f7fb] px-3.5 py-3 text-[12px] leading-[1.8]">
        <p>
          Ориентир: <strong>≈ {money(stay.estimated_room_night_rub)}</strong> за
          номер / ночь
        </p>
        <p className="mt-[3px] text-muted">
          {stay.rooms} ном. × {nightsLabel(stay.nights)} · ≈{" "}
          {money(stay.estimated_total_rub)} за поездку
        </p>
        <p className="mt-[3px] text-[11px] text-muted">
          Учтено в бюджете; запас указан отдельно. До 2 гостей в номере,
          размещение детей уточняйте.
        </p>
      </div>
      <p className="mt-3 text-[11px] leading-[1.8] text-muted">
        {ACCOMMODATION_DISCLAIMER}
      </p>
      <div className={`mt-2 divide-x-0 divide-y divide-solid divide-[var(--line)] ${stay.hotels.length ? "mb-3.5 border-x-0 border-t-0 border-b border-solid border-[var(--line)]" : ""}`}>
        {stay.hotels.map((hotel) => (
          <article
            key={hotel.id}
            data-ui="hotel-card"
            className="py-3.5 first:pt-2.5"
          >
            <h3 className="text-[13px] font-bold leading-[1.6] wrap-anywhere">
              {hotel.name}
            </h3>
            <p className="mt-[3px] text-[11px] leading-[1.8] text-muted">
              {hotel.kind === "hotel" ? "Гостиница" : "Гостевой дом"} ·{" "}
              {hotel.distance_km.toLocaleString("ru-RU")} км от центра по прямой
            </p>
            {hotel.address && (
              <p className="mt-1 text-[12px] leading-[1.7] text-[#687389] wrap-anywhere">
                {hotel.address}
              </p>
            )}
            <div className="mt-1 flex flex-wrap items-center gap-x-4.5">
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
          className="mt-3.5 text-[12px] leading-[1.8] text-[#687389]"
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
    </section>
  );
}
