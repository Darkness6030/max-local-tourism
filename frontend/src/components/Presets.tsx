import {
  eyebrowStyles,
  iconButtonStyles,
  packingCheckboxStyles,
  packingListStyles,
  presetInfoCardStyles,
  programDayHeadingStyles,
  programTimelineStyles,
  sectionHeadingStyles,
  softBlueIconStyles,
  softLavenderIconStyles,
} from "../ui-styles";
import { useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  Backpack,
  CalendarDays,
  Check,
  MapPin,
  TrainFront,
  Users,
  Wallet,
} from "lucide-react";
import { tripPresets, type TripPreset } from "../presets";
import { money, openExternal } from "../lib";
import { Notice, Primary } from "./UI";

export function PresetCards({
  origin,
  onOpen,
}: {
  origin: string;
  onOpen: (preset: TripPreset) => void;
}) {
  return (
    <section
      data-ui="preset-section"
      className="mt-8 preset-mobile:mt-6"
      aria-labelledby="preset-heading"
    >
      <div data-ui="section-heading" className={sectionHeadingStyles}>
        <div>
          <span data-ui="eyebrow" className={eyebrowStyles}>
            МОЖНО ПРОСТО ВЫБРАТЬ
          </span>
          <h2 id="preset-heading">
            Идеи поездок {origin === "Москва" ? "из Москвы" : "из Петербурга"}
          </h2>
        </div>
        <span>Готовые маршруты</span>
      </div>
      <div
        data-ui="preset-grid"
        className="grid grid-cols-[repeat(2,_minmax(0,_1fr))] gap-4
          preset-tablet:grid-cols-[repeat(2,_minmax(0,_1fr))] preset-mobile:gap-3"
      >
        {tripPresets
          .filter((preset) => preset.origin === origin)
          .map((preset) => (
            <button
              data-ui="preset-card"
              className="flex flex-col p-0 text-left [border:1px_solid_var(--line)] rounded-[22px] bg-white
                overflow-hidden [transition:box-shadow_0.2s,_border-color_0.2s]
                preset-mobile:rounded-[18px] [&:hover]:border-[#c7d1ff]
                [&:hover]:[box-shadow:0_8px_24px_#30426b10] [&:hover_img]:[transform:scale(1.035)]"
              key={preset.id}
              onClick={() => onOpen(preset)}
              aria-label={`Открыть маршрут: ${preset.city}`}
            >
              <span
                data-ui="preset-card-photo"
                className="relative block w-full overflow-hidden [&_img]:w-full [&_img]:h-auto [&_img]:max-h-60
                  [&_img]:[aspect-ratio:1.55] [&_img]:object-cover [&_img]:object-[center_60%]
                  [&_img]:[transition:transform_0.35s]"
              >
                <img
                  src={preset.photo}
                  alt={preset.photoAlt}
                  loading="lazy"
                  decoding="async"
                  width={1280}
                  height={960}
                />
                <span
                  data-ui="preset-duration"
                  className="absolute bottom-2.5 left-2.5 flex items-center gap-[5px] py-1.5 px-[9px]
                    rounded-[20px] bg-[#fffffff2] text-[10px] font-[750]"
                >
                  <CalendarDays size={12} />
                  {preset.days.length === 1 ? "1 день" : "2 дня"}
                </span>
              </span>
              <span
                data-ui="preset-card-copy"
                className="flex flex-1 flex-col p-4 preset-mobile:p-3 [&_>_small]:text-muted
                  [&_>_small]:text-[10px] [&_>_strong]:block [&_>_strong]:mt-1.5 [&_>_strong]:mx-0
                  [&_>_strong]:mb-2 [&_>_strong]:text-[19px] [&_>_strong]:font-extrabold
                  [&_>_strong]:tracking-[-0.5px] [&_>_strong]:leading-[1.3]
                  preset-mobile:[&_>_strong]:text-[17px]"
              >
                <small>
                  Из {preset.origin === "Москва" ? "Москвы" : "Петербурга"}
                </small>
                <strong>{preset.city}</strong>
                <span>{preset.tagline}</span>
                <span
                  data-ui="preset-card-link"
                  className="[[data-ui~=preset-card-copy]_>_span:not(&)]:text-[12px]
                    [[data-ui~=preset-card-copy]_>_span:not(&)]:leading-[1.7]
                    [[data-ui~=preset-card-copy]_>_span:not(&)]:text-[#687389]
                    [[data-ui~=preset-card-copy]_>_span:not(&)]:mb-4
                    preset-mobile:[[data-ui~=preset-card-copy]_>_span:not(&)]:text-[11px] flex
                    items-center justify-between gap-1 mt-auto text-[11px] font-[750] text-brand
                    preset-mobile:text-[10px]"
                >
                  Смотреть план <ArrowUpRight size={17} />
                </span>
              </span>
            </button>
          ))}
      </div>
    </section>
  );
}

export function PresetDetail({
  preset,
  onBack,
  onUse,
  hasActiveJob,
}: {
  preset: TripPreset;
  onBack: () => void;
  onUse: () => void;
  hasActiveJob: boolean;
}) {
  const [error, setError] = useState("");
  const [packed, setPacked] = useState<string[]>([]);
  const open = (url: string) => {
    try {
      Promise.resolve(openExternal(url)).catch(() =>
        setError("Не удалось открыть ссылку. Попробуйте ещё раз."),
      );
    } catch {
      setError("Не удалось открыть ссылку. Попробуйте ещё раз.");
    }
  };
  return (
    <article data-ui="preset-detail" className="max-w-237.5 m-auto">
      <div
        data-ui="preset-top"
        className="flex items-center justify-between h-17 gap-3 preset-mobile:h-15 [&_>_span]:text-[10px]
          [&_>_span]:font-[750] [&_>_span]:text-muted [&_>_span]:tracking-[0.6px]"
      >
        <button
          data-ui="icon-button"
          className={iconButtonStyles}
          onClick={onBack}
          aria-label="На главную"
        >
          <ArrowLeft size={22} />
        </button>
        <span>ГОТОВЫЙ МАРШРУТ</span>
        <span
          data-ui="preset-top-days"
          className="[[data-ui~=preset-top]_>_span&]:text-brand [[data-ui~=preset-top]_>_span&]:tracking-[0]"
        >
          {preset.days.length === 1 ? "1 день" : "2 дня"}
        </span>
      </div>
      <img
        data-ui="preset-cover"
        className="w-full h-75 object-cover object-[center_60%] rounded-[26px] preset-mobile:h-55
          preset-mobile:rounded-[22px] preset-short:h-47.5"
        src={preset.photo}
        alt={preset.photoAlt}
        width={1280}
        height={960}
      />
      <header
        data-ui="preset-intro"
        className="py-6 px-0 preset-mobile:py-5 preset-mobile:px-0 [&_h1]:my-3 [&_h1]:mx-0 [&_h1]:text-[34px]
          [&_h1]:tracking-[-1.3px] [&_h1]:leading-[1.25] preset-mobile:[&_h1]:text-[28px]
          preset-mobile:[&_h1]:tracking-[-0.9px] [&_>_p]:max-w-172.5 [&_>_p]:text-[#687389]
          [&_>_p]:text-[14px] [&_>_p]:leading-[1.8]"
      >
        <span data-ui="eyebrow" className={eyebrowStyles}>
          {preset.origin} → {preset.city}
        </span>
        <h1 id="preset-title">{preset.title}</h1>
        <p>{preset.summary}</p>
        <div
          data-ui="preset-facts"
          className="flex flex-wrap gap-[10px_18px] mt-4.5 [&_>_span]:flex [&_>_span]:items-center
            [&_>_span]:gap-1.5 [&_>_span]:text-[11px] [&_>_span]:text-[#687389] [&_svg]:text-brand"
        >
          <span>
            <CalendarDays size={15} />
            {preset.days.length === 1 ? "На один день" : "С одной ночёвкой"}
          </span>
          <span>
            <Users size={15} />
            Для двоих
          </span>
          <span>
            <Wallet size={15} />
            Ориентир ≈ {money(preset.budgetRub)}
          </span>
        </div>
      </header>
      {error && (
        <Notice error onClose={() => setError("")}>
          {error}
        </Notice>
      )}
      <div
        data-ui="preset-columns"
        className="grid grid-cols-[minmax(0,_1.5fr)_minmax(0,_1fr)] gap-7 [align-items:start]
          preset-mobile:grid-cols-[minmax(0,_1fr)] preset-mobile:gap-6"
      >
        <div
          data-ui="preset-program"
          className="[&_>_h2]:text-[22px] [&_>_h2]:tracking-[-0.7px]"
        >
          <h2>План уже есть</h2>
          <p
            data-ui="preset-help"
            className="mt-2 mx-0 mb-5 text-muted text-[12px] leading-[1.7]"
          >
            Время — ориентир для прогулки. Сеансы и билеты выбирайте на свою
            дату.
          </p>
          {preset.days.map((day, index) => (
            <section
              data-ui="preset-day"
              className="mt-6"
              key={day.title}
              aria-labelledby={`preset-day-${index}`}
            >
              <div
                data-ui="preset-day-heading"
                className={programDayHeadingStyles}
              >
                <span>0{index + 1}</span>
                <h3 id={`preset-day-${index}`}>{day.title}</h3>
              </div>
              <ol
                data-ui="preset-timeline"
                className={programTimelineStyles}
              >
                {day.stops.map((stop) => (
                  <li key={stop.time}>
                    <time>{stop.time}</time>
                    <h4>{stop.title}</h4>
                    <p>{stop.description}</p>
                    <a
                      href={`https://yandex.ru/maps/?text=${encodeURIComponent(stop.place + ", " + preset.city)}`}
                      onClick={(event) => {
                        event.preventDefault();
                        open(event.currentTarget.href);
                      }}
                    >
                      <MapPin size={14} />
                      <span>{stop.place}</span>
                      <ArrowUpRight size={14} />
                    </a>
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>
        <aside data-ui="preset-sidebar" className="grid gap-4">
          <section data-ui="preset-info-card" className={presetInfoCardStyles}>
            <span data-ui="soft-icon blue" className={softBlueIconStyles}>
              <Wallet size={22} />
            </span>
            <h2>Бюджет на месте</h2>
            <strong
              data-ui="preset-budget"
              className="block text-[28px] mb-2 tracking-[-1px]"
            >
              ≈ {money(preset.budgetRub)}
            </strong>
            <p>Ориентир на двоих, без дороги и проживания.</p>
            <dl>
              {preset.budgetItems.map((item) => (
                <div key={item.label}>
                  <dt>{item.label}</dt>
                  <dd>{money(item.amount)}</dd>
                </div>
              ))}
            </dl>
            <small>
              Это план расходов, а не цены билетов. Точную стоимость посещений
              проверьте у музеев.
            </small>
          </section>
          <section data-ui="preset-info-card" className={presetInfoCardStyles}>
            <span
              data-ui="soft-icon lavender"
              className={softLavenderIconStyles}
            >
              <TrainFront size={22} />
            </span>
            <h2>Как добраться</h2>
            <p>{preset.travel}</p>
            <p
              data-ui="preset-tip"
              className="mt-4 pt-4 [border-top:1px_solid_var(--line)]"
            >
              {preset.tip}
            </p>
          </section>
          <section
            data-ui="preset-info-card preset-packing-card"
            className="p-5.5 bg-white [border:1px_solid_var(--line)] rounded-[22px] [&_>_h2]:text-[17px]
              [&_>_h2]:mt-4 [&_>_h2]:mx-0 [&_>_h2]:mb-3 [&_>_h2]:tracking-[-0.3px] [&_p]:text-[12px]
              [&_p]:leading-[1.8] [&_p]:text-[#687389] [&_small]:text-[12px] [&_small]:leading-[1.8]
              [&_small]:text-[#687389] [&_dl]:my-4 [&_dl]:mx-0 [&_dl]:py-3 [&_dl]:px-0
              [&_dl]:[border-block:1px_solid_var(--line)] [&_dl_>_div]:flex
              [&_dl_>_div]:justify-between [&_dl_>_div]:gap-3 [&_dl_>_div]:py-[7px] [&_dl_>_div]:px-0
              [&_dl_>_div]:text-[12px] [&_dl_>_div]:leading-[1.5] [&_dd]:m-0 [&_dd]:whitespace-nowrap
              [&_dd]:font-[750] [[data-ui~=preset-info-card]&]:pb-3
              [[data-ui~=preset-info-card]&_>_h2]:mb-1"
          >
            <span data-ui="soft-icon blue" className={softBlueIconStyles}>
              <Backpack size={22} />
            </span>
            <h2>Взять с собой</h2>
            <div data-ui="packing-list" className={packingListStyles}>
              {preset.packing.map((item) => (
                <label
                  key={item}
                  data-ui={packed.includes(item) ? "packed" : ""}
                  className={
                    packed.includes(item)
                      ? "[[data-ui~=packing-list]_label&]:text-[#a9b0bf] [[data-ui~=packing-list]_label&]:[text-decoration:line-through]"
                      : ""
                  }
                >
                  <input
                    type="checkbox"
                    checked={packed.includes(item)}
                    onChange={() =>
                      setPacked((old) =>
                        old.includes(item)
                          ? old.filter((value) => value !== item)
                          : [...old, item],
                      )
                    }
                  />
                  <span
                    data-ui="packing-checkbox"
                    className={packingCheckboxStyles}
                  >
                    {packed.includes(item) && <Check size={12} />}
                  </span>
                  {item}
                </label>
              ))}
            </div>
          </section>
        </aside>
      </div>
      <section
        data-ui="preset-sources"
        className="[&_>_h2]:text-[22px] [&_>_h2]:tracking-[-0.7px] [border-top:1px_solid_var(--line)] mt-5 pt-5"
      >
        <h2>Места и билеты</h2>
        <p
          data-ui="preset-help"
          className="mt-2 mx-0 mb-5 text-muted text-[12px] leading-[1.7]"
        >
          Выберите время посещения и проверьте билеты на сайте места.
        </p>
        <ul
          data-ui="venue-list"
          className="grid gap-2.5 m-0 p-0 [list-style:none] [&_>_li]:flex [&_>_li]:items-center [&_>_li]:gap-3
            [&_>_li]:p-3.5 [&_>_li]:bg-white [&_>_li]:[border:1px_solid_var(--line)]
            [&_>_li]:rounded-[18px] loading-narrow:[&_>_li]:gap-2 loading-narrow:[&_>_li]:p-2.5
            [&_a]:flex [&_a]:items-center [&_a]:justify-center [&_a]:gap-1 [&_a]:shrink-0
            [&_a]:min-h-11 [&_a]:py-0 [&_a]:px-2.5 [&_a]:rounded-xl [&_a]:bg-[#f2f5ff]
            [&_a]:text-brand [&_a]:text-[12px] [&_a]:font-bold [&_a]:no-underline
            [&_a]:[transition:background_0.2s] [&_a:hover]:bg-[#e6ecff]"
        >
          {preset.sources.map((source) => (
            <li key={source.url}>
              <span
                data-ui="venue-icon"
                className="grid place-items-center size-9.5 rounded-xl text-brand bg-[#edf1ff] shrink-0
                  loading-narrow:size-7.5 loading-narrow:rounded-[10px]"
                aria-hidden="true"
              >
                <MapPin size={19} />
              </span>
              <div
                data-ui="venue-name"
                className="flex-1 min-w-0 [&_strong]:block [&_strong]:text-[13px] [&_strong]:leading-[1.5]
                  [&_small]:block [&_small]:mt-1 [&_small]:text-[11px] [&_small]:text-muted
                  [&_small]:wrap-anywhere"
              >
                <strong>{source.name}</strong>
                <small>
                  {new URL(source.url).hostname.replace(/^www\./, "")}
                </small>
              </div>
              <a
                href={source.url}
                aria-label={`Открыть сайт: ${source.name}`}
                onClick={(event) => {
                  event.preventDefault();
                  open(source.url);
                }}
              >
                Сайт <ArrowUpRight size={16} />
              </a>
            </li>
          ))}
        </ul>
      </section>
      <div
        data-ui="preset-actions"
        className="fixed z-[20] bottom-4 left-[50%] [transform:translateX(-50%)]
          w-[min(520px,_calc(100%_-_48px))] py-3 px-4 bg-[#fffffff5] [border:1px_solid_var(--line)]
          rounded-[22px] [backdrop-filter:blur(16px)] [box-shadow:0_4px_24px_#30426b0a]
          preset-mobile:left-0 preset-mobile:right-0 preset-mobile:bottom-0
          preset-mobile:[transform:none] preset-mobile:w-auto preset-mobile:rounded-[22px_22px_0_0]
          preset-mobile:bg-[#f8f9fc] preset-mobile:pt-3 preset-mobile:px-6
          preset-mobile:pb-[max(10px,_var(--app-safe-bottom))] [&_>_span]:block
          [&_>_span]:text-center [&_>_span]:text-[10px] [&_>_span]:text-muted [&_>_span]:leading-[1.6]
          [&_>_span]:mt-2"
      >
        <Primary id="use-preset" onClick={onUse}>
          {hasActiveJob ? "Вернуться к генерации" : "Настроить поездку"}
        </Primary>
        <span>Выберите даты — уточним погоду, дорогу и программу.</span>
      </div>
    </article>
  );
}
