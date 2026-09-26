import { BUDGET_DISCLAIMER, budgetItemCopy, tripNotices } from "../trip-copy";
import {
  activeStyles,
  eyebrowStyles,
  fieldLabelStyles,
  iconButtonStyles,
  inlineNoteStyles,
  packingCheckboxStyles,
  packingListStyles,
  primaryButtonStyles,
  programDayHeadingStyles,
  programTimelineStyles,
  softBlueIconStyles,
  softLavenderIconStyles,
  textButtonStyles,
} from "../ui-styles";
import { useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  ArrowLeft,
  ArrowUpRight,
  Backpack,
  CalendarDays,
  Check,
  ChevronDown,
  CloudSun,
  Copy,
  Footprints,
  Info,
  MapPin,
  Share2,
  TrainFront,
  Users,
  Wallet,
} from "lucide-react";
import type { TransportOption, TripPlan } from "../types";
import { api, dateLabel, money, openExternal, safeUrl, timeLabel } from "../lib";
import { AccommodationCard } from "./AccommodationCard";
import { Notice } from "./UI";

const RESULT_TABS = [
  { value: "program", label: "Программа", Icon: Footprints },
  { value: "transport", label: "Дорога", Icon: TrainFront },
  { value: "budget", label: "Бюджет", Icon: Wallet },
] as const;
type Tab = (typeof RESULT_TABS)[number]["value"];
export function TripResult({
  plan,
  onBack,
  onEdit,
  initData,
  onPlanChange,
}: {
  plan: TripPlan;
  onBack: () => void;
  onEdit: () => void;
  initData: string;
  onPlanChange: (plan: TripPlan) => void;
}) {
  const [tab, setTab] = useState<Tab>("program");
  const [dayIndex, setDayIndex] = useState(0);
  const [message, setMessage] = useState("");
  const [shareText, setShareText] = useState("");
  const [sharing, setSharing] = useState(false);
  const [shareReady, setShareReady] = useState(false);
  const [manualCopy, setManualCopy] = useState(false);
  const packed = plan.packed_items ?? [];
  const packing = useRef({
    confirmed: plan,
    pending: new Map<number, boolean>(),
    saving: false,
  });
  const publishPacking = () => {
    const { confirmed, pending } = packing.current;
    const items = new Set(confirmed.packed_items ?? []);

    pending.forEach((checked, index) => {
      if (checked) items.add(index);
      else items.delete(index);
    });

    onPlanChange({ ...confirmed, packed_items: [...items].sort((a, b) => a - b) });
  };
  const togglePacked = async (itemIndex: number) => {
    const state = packing.current;
    const checked = state.pending.get(itemIndex)
      ?? (state.confirmed.packed_items ?? []).includes(itemIndex);
    state.pending.set(itemIndex, !checked);
    publishPacking();

    if (state.saving) return;

    state.saving = true;
    // Serialize writes; later clicks remain visible while a response is in flight.
    while (state.pending.size) {
      const [index, value] = state.pending.entries().next().value!;
      try {
        state.confirmed = await api<TripPlan>(`/trips/${plan.id}/packing`, initData, {
          method: "PATCH",
          body: JSON.stringify({ item_index: index, checked: value }),
        });
      } catch (error) {
        setMessage((error as Error).message);
      }

      if (state.pending.get(index) === value) state.pending.delete(index);
      publishPacking();
    }

    state.saving = false;
  };
  const [checksOpen, setChecksOpen] = useState(false);
  const reducedMotion = useReducedMotion();
  const weather =
    plan.weather.days[Math.min(dayIndex, plan.weather.days.length - 1)];
  const budgetItems = plan.budget.items.map((item) => budgetItemCopy(item, plan));

  const external = (url: string) => {
    try {
      Promise.resolve(openExternal(url)).catch(() =>
        setMessage(
          "Не удалось открыть ссылку. Попробуйте во внешнем браузере.",
        ),
      );
    } catch {
      setMessage("Не удалось открыть ссылку.");
    }
  };
  const prepareShare = async () => {
    if (sharing) return;
    setSharing(true);
    try {
      const result = await api<{ text: string }>(`/trips/${plan.id}/share`, initData, { method: "POST" });
      setShareText(result.text);
      setShareReady(true);
      setMessage("");
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setSharing(false);
    }
  };
  const share = () => {
    setShareReady(false);
    // Keep this synchronous until the Bridge call to retain the user gesture.
    const bridge = window.WebApp;
    if (bridge?.initData && bridge.shareMaxContent) {
      try {
        Promise.resolve(
          bridge.shareMaxContent({ text: shareText }),
        ).catch(() =>
          setMessage(
            "Шеринг недоступен в этом клиенте. Скопируйте план и отправьте его в чат.",
          ),
        );
      } catch {
        setMessage("Не удалось открыть шеринг. Попробуйте скопировать план.");
      }
    } else {
      window.open(
        `https://max.ru/:share?text=${encodeURIComponent(shareText)}`,
        "_blank",
        "noopener,noreferrer",
      );
      setMessage(
        "Выберите чат в MAX. Если окно не открылось, скопируйте план.",
      );
    }
  };
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(shareText || plan.share_text);
      setMessage("План скопирован. Отправьте его тем, кого берёте с собой.");
    } catch {
      setManualCopy(true);
      setMessage("Автоматическое копирование недоступно. Выделите текст ниже.");
    }
  };
  return (
    <div
      data-ui="result-page"
      className="max-w-250 my-0 mx-auto pb-0 mobile:pb-0"
    >
      <div
        data-ui="result-top"
        className="flex items-center justify-between -mt-2 mx-0 mb-5 mobile:h-[73px] mobile:my-0
          mobile:mx-[-7px] mobile:pt-[env(safe-area-inset-top)] [&_>_span]:text-[11px]
          [&_>_span]:font-[750] [&_>_span]:tracking-[1.2px] [&_>_span]:text-[#929bad]
          mobile:[&_>_span]:text-[11px] mobile:[&_>_span]:tracking-[1px]"
      >
        <button
          data-ui="icon-button"
          className={iconButtonStyles}
          onClick={onBack}
          aria-label="На главную"
        >
          <ArrowLeft size={22} />
        </button>
        <span>ВАШЕ МАЛЕНЬКОЕ ПУТЕШЕСТВИЕ</span>
        <button
          data-ui="icon-button"
          className={iconButtonStyles}
          onClick={copy}
          aria-label="Скопировать план"
        >
          <Copy size={19} />
        </button>
      </div>
      {plan.destination_photo && (
        <DestinationPhoto
          key={plan.id}
          photo={plan.destination_photo}
          city={plan.destination.title}
        />
      )}
      <section
        data-ui="result-hero"
        className="pt-0 px-2 pb-2 mobile:pt-0 mobile:px-[1px] [&_h1]:text-[38px] [&_h1]:tracking-[-1.6px]
          [&_h1]:font-extrabold [&_h1]:leading-[1.24] [&_h1]:max-w-190 [&_h1]:mt-[13px] [&_h1]:mx-0
          [&_h1]:mb-4.5 [&_h1]:wrap-anywhere tablet:[&_h1]:text-[32px] mobile:[&_h1]:text-[28px]
          mobile:[&_h1]:tracking-[-1px] mobile:[&_h1]:leading-[1.28] mobile:[&_h1]:mt-[13px]
          mobile:[&_h1]:mx-0 mobile:[&_h1]:mb-[17px] narrow:[&_h1]:text-[26px] [&_>_p]:text-[12px]
          [&_>_p]:leading-[1.9] [&_>_p]:max-w-180 [&_>_p]:mt-4.5 [&_>_p]:mx-0 [&_>_p]:mb-[5px]
          mobile:[&_>_p]:text-[11px] mobile:[&_>_p]:leading-[1.9] mobile:[&_>_p]:mt-4
          [&_>_p]:text-[#687389] mobile-copy:[&_>_p]:text-[14px]"
      >
        <span
          data-ui="result-route"
          className="flex items-center gap-[9px] text-[11px] font-[650] text-[#8994af] mobile:text-[11px]
            mobile:gap-1.5 mobile-type:flex-wrap [&_>_svg]:text-brand"
        >
          <MapPin size={15} />
          {plan.origin.title}
          <span>→</span>
          {plan.destination.title}
        </span>
        <h1 id="result-title">{plan.title}</h1>
        <div
          data-ui="result-facts"
          className="flex flex-wrap gap-[9px] mobile:gap-1.5 mobile-type:text-[12px] [&_>_span]:flex
            [&_>_span]:items-center [&_>_span]:gap-1.5 [&_>_span]:text-[11px] [&_>_span]:bg-white
            [&_>_span]:[border:1px_solid_var(--line)] [&_>_span]:rounded-[9px] [&_>_span]:py-[7px]
            [&_>_span]:px-2.5 [&_>_span]:text-[#7e89a2] mobile:[&_>_span]:text-[11px]
            mobile:[&_>_span]:py-[7px] mobile:[&_>_span]:px-2 mobile:[&_>_span]:gap-[5px]
            [&_>_span_>_svg]:text-[#a1acc2] mobile:[&_>_span_>_svg]:size-3"
        >
          <span>
            <CalendarDays size={15} />
            {dateLabel(plan.request.start_date)}
          </span>
          <span>
            <Users size={15} />
            {plan.request.travelers} чел.
          </span>
          <span>
            <Wallet size={15} />≈ {money(plan.budget.estimated_total_rub)}
          </span>
        </div>
        <p>{plan.summary}</p>
        <button
          data-ui="text-button"
          className={textButtonStyles}
          onClick={onEdit}
        >
          Изменить пожелания <ArrowUpRight size={16} />
        </button>
      </section>
      {message && <Notice onClose={() => setMessage("")}>{message}</Notice>}
      {shareReady && (
        <div role="dialog" aria-label="Поделиться маршрутом" className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-5">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-xl">
            <h2 className="mb-3 text-xl font-bold">Поделиться маршрутом</h2>
            <p className="mb-5 text-sm text-muted">В конце сообщения будет ссылка на бота. По ней друзья сохранят маршрут себе и сразу откроют его.</p>
            <button className={primaryButtonStyles} onClick={share}>Отправить в MAX</button>
            <button className={textButtonStyles} onClick={() => { setShareReady(false); void copy(); }}>Копировать со ссылкой</button>
            <button className={textButtonStyles} onClick={() => setShareReady(false)}>Закрыть</button>
          </div>
        </div>
      )}
      {manualCopy && (
        <label data-ui="field-label" className={fieldLabelStyles}>
          Текст поездки
          <textarea
            readOnly
            rows={5}
            value={shareText || plan.share_text}
            onFocus={(event) => event.target.select()}
          />
        </label>
      )}
      <div
        data-ui="result-columns"
        className="grid grid-cols-[minmax(0,_1.7fr)_minmax(0,_1fr)] gap-6 [align-items:start] tablet:gap-5
          tablet:grid-cols-[1.6fr_1fr] mobile:flex mobile:flex-col mobile:gap-6 mobile-spacing:gap-6"
      >
        <div data-ui="result-main" className="mobile:w-full">
          <div
            data-ui="result-tabs"
            className="relative flex gap-1 bg-[#eef1f8] rounded-[14px] p-[5px] mb-[25px] mobile:sticky
              mobile:top-1.5 mobile:z-[10] mobile:mb-5.5 mobile:p-1 mobile:rounded-[13px]
              mobile:bg-[#ecf0f9] mobile:[box-shadow:0_0_0_6px_#f8f9fc] [&_>_button]:flex
              [&_>_button]:justify-center [&_>_button]:items-center [&_>_button]:gap-[7px]
              [&_>_button]:flex-1 [&_>_button]:relative [&_>_button]:bg-transparent
              [&_>_button]:text-[#8b94a9] [&_>_button]:text-[11px] [&_>_button]:min-h-[43px]
              [&_>_button]:rounded-[10px] [&_>_button]:z-0 mobile:[&_>_button]:text-[11px]
              mobile:[&_>_button]:gap-1.5 mobile:[&_>_button]:min-h-[43px]
              mobile:[&_>_button_>_svg]:size-[15px] mobile-type:[&_button]:text-[12px]
              mobile-type:[&_button]:py-3 mobile-type:[&_button]:px-[7px]
              mobile-type:[&_button]:gap-1.5"
            role="tablist"
            aria-label="Информация о поездке"
            onKeyDown={(event) => {
              const tabs = RESULT_TABS.map(({ value }) => value);
              if (["ArrowLeft", "ArrowRight"].includes(event.key)) {
                event.preventDefault();
                const next =
                  tabs[
                    (tabs.indexOf(tab) +
                      (event.key === "ArrowRight" ? 1 : tabs.length - 1)) %
                      tabs.length
                  ];
                setTab(next);
                document.getElementById(`tab-${next}`)?.focus();
              }
            }}
          >
            {RESULT_TABS.map(({ value, label, Icon }) => (
              <button
                id={`tab-${value}`}
                role="tab"
                key={value}
                aria-selected={tab === value}
                aria-controls="result-panel"
                tabIndex={tab === value ? 0 : -1}
                onClick={() => setTab(value)}
                data-ui={tab === value ? "active" : ""}
                className={tab === value ? activeStyles : ""}
              >
                <Icon size={17} />
                {label}
                {tab === value && (
                  <motion.span
                    layoutId="result-tab"
                    data-ui="tab-highlight"
                    className="absolute top-0 right-0 bottom-0 left-0 rounded-[10px] bg-white
                      [box-shadow:0_2px_6px_#26355409] z-[-1]"
                  />
                )}
              </button>
            ))}
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              id="result-panel"
              role="tabpanel"
              aria-labelledby={`tab-${tab}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.16 }}
            >
              {tab === "program" && (
                <>
                  {plan.itinerary.length > 1 && (
                    <div
                      data-ui="day-selector"
                      className="flex gap-[7px] mb-5 [&_>_button]:py-[9px] [&_>_button]:px-[15px]
                        [&_>_button]:rounded-[11px] [&_>_button]:[border:1px_solid_var(--line)]
                        [&_>_button]:bg-white [&_>_button]:text-[11px] [&_>_button]:text-[#9099ac]
                        [&_>_button_>_span]:block [&_>_button_>_span]:text-[11px]
                        [&_>_button_>_span]:mt-1"
                    >
                      {plan.itinerary.map((day, i) => (
                        <button
                          key={day.date}
                          data-ui={dayIndex === i ? "active" : ""}
                          className={dayIndex === i ? activeStyles : ""}
                          onClick={() => setDayIndex(i)}
                        >
                          День {i + 1}
                          <span>
                            {dateLabel(day.date, {
                              day: "numeric",
                              month: "short",
                            })}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                  <div data-ui="timeline-heading" className={programDayHeadingStyles}>
                    <span>{String(dayIndex + 1).padStart(2, "0")}</span>
                    <h3 id="program-day-title">{plan.itinerary[dayIndex].title}</h3>
                  </div>
                  <ol
                    data-ui="timeline"
                    className={programTimelineStyles}
                    aria-labelledby="program-day-title"
                  >
                    {plan.itinerary[dayIndex].items.map((item, i) => (
                      <motion.li
                        data-ui="timeline-item"
                        key={`${dayIndex}-${i}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(i * 0.055, 0.3) }}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <time>{item.start_time} — {item.end_time}</time>
                          <span
                            data-ui="location-tag"
                            className={`rounded-[5px] px-1.5 py-1 text-[10px] whitespace-nowrap ${
                              item.indoor
                                ? "bg-[#f2effc] text-[#9a88b6]"
                                : "bg-[#eff5e9] text-[#7d9777]"
                            }`}
                          >
                            {item.indoor ? "Внутри" : "На воздухе"}
                          </span>
                        </div>
                        <h4>{item.title}</h4>
                        <p>{item.description}</p>
                        <a
                          href={`https://yandex.ru/maps/?text=${encodeURIComponent(item.place + ", " + plan.destination.title)}`}
                          onClick={(event) => {
                            event.preventDefault();
                            external(event.currentTarget.href);
                          }}
                        >
                          <MapPin size={14} />
                          <span>{item.place}</span>
                          <ArrowUpRight size={14} />
                        </a>
                        {item.estimated_cost_rub > 0 && (
                          <span
                            data-ui="activity-price"
                            className="block text-[11px] font-[650] text-[#7e89a1] mobile:text-[12px]"
                          >
                            ≈ {money(item.estimated_cost_rub)}
                          </span>
                        )}
                      </motion.li>
                    ))}
                  </ol>
                  {plan.request.days > 1 && plan.accommodation && (
                    <AccommodationCard
                      stay={plan.accommodation}
                      external={external}
                    />
                  )}
                  <section
                    data-ui="packing-card"
                    className="mt-6 pt-5.5 px-5.5 [border:1px_solid_var(--line)] rounded-[20px] bg-white
                      mobile:pt-[19px] mobile:px-[19px] mobile:mt-4 mobile:rounded-[18px] pb-3.5"
                  >
                    <div
                      data-ui="section-title"
                      className="flex gap-3 items-center [&_h2]:text-[14px] [&_h2]:font-[750]
                        mobile:[&_h2]:text-[13px] mobile-type:[&_h2]:text-[13px] [&_p]:text-[11px]
                        [&_p]:text-[#9a9fb0] [&_p]:mt-[5px] mobile:[&_p]:text-[11px]"
                    >
                      <span
                        data-ui="soft-icon lavender"
                        className={softLavenderIconStyles}
                      >
                        <Backpack size={22} />
                      </span>
                      <div>
                        <h2>Не забудьте взять</h2>
                        <p>Небольшие вещи для хорошего дня</p>
                      </div>
                    </div>
                    <div data-ui="packing-list" className={packingListStyles}>
                      {plan.packing_list.map((item, itemIndex) => (
                        <label
                          key={itemIndex}
                          data-ui={packed.includes(itemIndex) ? "packed" : ""}
                          className={
                            packed.includes(itemIndex)
                              ? "[[data-ui~=packing-list]_label&]:text-[#a9b0bf] [[data-ui~=packing-list]_label&]:[text-decoration:line-through]"
                              : ""
                          }
                        >
                          <input
                            type="checkbox"
                            checked={packed.includes(itemIndex)}
                            onChange={() => void togglePacked(itemIndex)}
                          />
                          <span
                            data-ui="packing-checkbox"
                            className={packingCheckboxStyles}
                          >
                            {packed.includes(itemIndex) && <Check size={13} />}
                          </span>
                          {item}
                        </label>
                      ))}
                    </div>
                  </section>
                </>
              )}
              {tab === "transport" && (
                <section
                  data-ui="transport-panel"
                  className="[&_>_h2]:text-[20px] [&_>_h2]:tracking-[-0.6px] [&_>_h2]:font-[750]
                    [&_>_h2]:mb-2.5 mobile:[&_>_h2]:text-[20px] mobile:[&_>_h2]:leading-[1.4]
                    [&_>_p]:text-[11px] [&_>_p]:leading-[1.9] [&_>_p]:mb-5 mobile:[&_>_p]:text-[11px]
                    mobile-type:[&_>_p]:text-[14px]"
                >
                  <h2>Дорога — часть путешествия</h2>
                  <p
                    data-ui="muted"
                    className="text-muted [[data-ui~=text-button]&]:text-muted"
                  >
                    Время рейсов из расписаний. Перед отправлением проверьте
                    изменения у перевозчика.
                  </p>
                  {plan.request.has_car && (
                    <Notice>
                      Вы выбрали автомобиль. Пробки не учтены; найденные рейсы
                      ниже — альтернатива.
                    </Notice>
                  )}
                  {plan.map_url && safeUrl(plan.map_url) && (
                    <button
                      id="map-link"
                      data-ui="map-button"
                      className="w-full flex items-center gap-[13px] p-4 [border:1px_solid_#e0e6f7]
                        bg-[#f3f6ff] rounded-[18px] text-left text-brand mobile:p-3.5 mobile:gap-2.5
                        [&_>_span:nth-child(2)]:flex-1 [&_strong]:block [&_strong]:text-[11px]
                        mobile:[&_strong]:text-[11px] mobile-type:[&_strong]:text-[13px]
                        [&_small]:block [&_small]:text-[11px] [&_small]:mt-[5px]
                        [&_small]:text-[#8f9cb9] mobile:[&_small]:text-[11px]"
                      onClick={() => external(plan.map_url!)}
                    >
                      <span
                        data-ui="soft-icon blue"
                        className={softBlueIconStyles}
                      >
                        <MapPin size={23} />
                      </span>
                      <span>
                        <strong>Открыть маршрут на карте</strong>
                        <small>Яндекс Карты</small>
                      </span>
                      <ArrowUpRight size={22} />
                    </button>
                  )}
                  {plan.transport ? (
                    <>
                      {(
                        [
                          ["Туда", plan.transport.outbound],
                          ["Обратно", plan.transport.return_trip],
                        ] as [string, TransportOption[]][]
                      ).map(([title, options]) => (
                        <div
                          key={title}
                          data-ui="transport-direction"
                          className="[&_>_h3]:text-[14px] [&_>_h3]:font-[750] [&_>_h3]:mt-[25px] [&_>_h3]:mx-0
                            [&_>_h3]:mb-[13px] [&_>_p]:text-[11px]"
                        >
                          <h3>{title}</h3>
                          {!options.length && (
                            <p
                              data-ui="muted"
                              className="text-muted [[data-ui~=text-button]&]:text-muted"
                            >
                              Подходящих рейсов не найдено.
                            </p>
                          )}
                          {options.map((option, i) => (
                            <div
                              data-ui="train-card"
                              className="[border:1px_solid_var(--line)] rounded-[18px] pt-[19px] px-[19px] pb-0
                                bg-white mt-3 mobile:pt-[17px] mobile:px-[17px] mobile:pb-0"
                              key={i}
                            >
                              <div
                                data-ui="train-card-top"
                                className="flex items-center gap-2 text-[11px] text-[#8e9ab1]
                                  mobile:text-[11px] mobile-type:gap-2 [&_small]:ml-auto
                                  [&_small]:text-[11px] [&_svg]:text-[#8295bf]"
                              >
                                <TrainFront size={18} />
                                <span>
                                  {option.has_transfers
                                    ? "С пересадкой"
                                    : "Без пересадок"}
                                </span>
                                <small>{option.duration_minutes} мин</small>
                              </div>
                              <div
                                data-ui="train-times"
                                className="flex justify-between gap-[15px] items-start my-4.5 mx-0
                                  [&_>_div]:flex-1 [&_>_div]:min-w-0 [&_>_div:last-child]:text-right
                                  [&_strong]:text-[23px] [&_strong]:font-[650]
                                  [&_strong]:tracking-[-0.5px] mobile:[&_strong]:text-[23px]
                                  [&_span]:block [&_span]:text-[11px] [&_span]:text-[#a2aabd]
                                  [&_span]:mt-[3px] [&_small]:block [&_small]:text-[11px]
                                  [&_small]:text-[#8b96aa] [&_small]:leading-[1.6] [&_small]:mt-[7px]
                                  mobile:[&_small]:text-[11px] mobile-type:[&_small]:text-[13px]"
                              >
                                <div>
                                  <strong>{timeLabel(option.departure)}</strong>
                                  <span>
                                    {dateLabel(option.departure.slice(0, 10), {
                                      day: "numeric",
                                      month: "short",
                                    })}
                                  </span>
                                  <small>{option.from_station}</small>
                                </div>
                                <span
                                  data-ui="train-line"
                                  className="[[data-ui~=train-times]_>_&]:[flex:0.6]
                                    [[data-ui~=train-times]_>_&]:h-[1px]
                                    [[data-ui~=train-times]_>_&]:mt-[17px]
                                    [[data-ui~=train-times]_>_&]:bg-[#dce2ef]
                                    [[data-ui~=train-times]_>_&]:relative [&::before]:[content:'']
                                    [&::before]:size-1 [&::before]:rounded-[50%]
                                    [&::before]:bg-[#bcc6de] [&::before]:absolute
                                    [&::before]:top-[-1.5px] [&::after]:[content:''] [&::after]:size-1
                                    [&::after]:rounded-[50%] [&::after]:bg-[#bcc6de]
                                    [&::after]:absolute [&::after]:top-[-1.5px] [&::after]:right-0"
                                />
                                <div>
                                  <strong>{timeLabel(option.arrival)}</strong>
                                  <span>
                                    {dateLabel(option.arrival.slice(0, 10), {
                                      day: "numeric",
                                      month: "short",
                                    })}
                                  </span>
                                  <small>{option.to_station}</small>
                                </div>
                              </div>
                              <div
                                data-ui="train-bottom"
                                className="flex justify-between items-center [border-top:1px_dashed_#e5e9f2]
                                  py-2 px-0 gap-2.5 [&_>_span]:text-[11px] [&_>_span]:text-[#838ea6]
                                  mobile:[&_>_span]:text-[11px] mobile-type:[&_>_span]:text-[12px]"
                              >
                                <span>
                                  {option.price_rub == null
                                    ? "Цена у перевозчика"
                                    : `от ${money(option.price_rub)}`}
                                </span>
                                <button
                                  data-ui="text-button"
                                  className={textButtonStyles}
                                  onClick={() => external(option.buy_url)}
                                >
                                  Расписание <ArrowUpRight size={15} />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ))}
                    </>
                  ) : (
                    <div
                      data-ui="empty-inline"
                      className="text-center py-9 px-[15px] text-[#a0acc2] [&_>_svg]:mt-auto [&_>_svg]:mx-auto
                        [&_>_svg]:mb-3.5 [&_h3]:text-[14px] [&_h3]:font-[650] [&_p]:text-[11px]
                        [&_p]:leading-[1.8] [&_p]:mt-[9px]"
                    >
                      <TrainFront size={30} />
                      <h3>Расписание не найдено</h3>
                      <p>
                        Проверьте варианты транспорта перед поездкой
                        самостоятельно.
                      </p>
                    </div>
                  )}
                </section>
              )}
              {tab === "budget" && (
                <section
                  id="budget"
                  data-ui="budget-panel"
                  className="bg-white [border:1px_solid_var(--line)] rounded-[23px] p-[27px] mobile:py-[23px]
                    mobile:px-5 mobile:rounded-[20px] [&_>_p]:text-[11px]"
                >
                  <span data-ui="eyebrow" className={eyebrowStyles}>
                    ПРИМЕРНАЯ СТОИМОСТЬ НА ВСЕХ
                  </span>
                  <div
                    data-ui="total-cost"
                    className="text-[42px] font-[750] tracking-[-1.7px] mt-[15px] mx-0 mb-[7px]
                      mobile:text-[38px]"
                  >
                    {money(plan.budget.estimated_total_rub)}
                  </div>
                  <p
                    data-ui="muted"
                    className="text-muted [[data-ui~=text-button]&]:text-muted"
                  >
                    {money(plan.budget.per_person_rub)} на человека
                  </p>
                  <div
                    data-ui="budget-meter"
                    className="h-[7px] rounded-[10px] bg-[#edf0f7] mt-6 overflow-hidden [&_>_span]:block
                      [&_>_span]:h-full [&_>_span]:bg-[#6d87e8] [&_>_span]:rounded-[10px]"
                  >
                    <span
                      style={{
                        width: `${Math.min((plan.budget.estimated_total_rub / plan.budget.limit_rub) * 100, 100)}%`,
                      }}
                      data-ui={!plan.budget.within_budget ? "exceeded" : ""}
                      className={
                        !plan.budget.within_budget
                          ? "[[data-ui~=budget-meter]_>_span&]:bg-[#e6a576]"
                          : ""
                      }
                    />
                  </div>
                  <div
                    data-ui="budget-limit"
                    className="flex justify-between gap-2.5 text-[11px] text-[#99a2b5] mt-[11px]
                      mobile:text-[11px] mobile-type:text-[12px] [&_strong]:font-[650]
                      [&_strong]:text-[#7e8ba4]"
                  >
                    <span>
                      {plan.budget.within_budget
                        ? "В рамках вашего бюджета"
                        : "Превышает ваш бюджет"}
                    </span>
                    <strong>{money(plan.budget.limit_rub)}</strong>
                  </div>
                  <div
                    data-ui="budget-items"
                    className="mt-6 [&_>_div]:flex [&_>_div]:justify-between [&_>_div]:[align-items:start]
                      [&_>_div]:gap-5 [&_>_div]:py-4 [&_>_div]:px-0
                      [&_>_div]:[border-bottom:1px_solid_var(--line)] [&_strong]:block
                      [&_strong]:text-[11px] [&_strong]:font-[650] mobile:[&_strong]:text-[11px]
                      mobile-type:[&_strong]:text-[13px] [&_small]:text-[11px] [&_small]:leading-[1.7]
                      [&_small]:text-[#a1a9ba] [&_small]:block [&_small]:mt-[5px]
                      mobile:[&_small]:text-[11px] mobile-type:[&_small]:text-[12px] [&_b]:text-[12px]
                      [&_b]:whitespace-nowrap mobile:[&_b]:text-[11px]"
                  >
                    {budgetItems.map((item, i) => (
                      <div key={i}>
                        <span>
                          <strong>{item.category}</strong>
                          {item.comment && <small>{item.comment}</small>}
                        </span>
                        <b>{money(item.amount_rub)}</b>
                      </div>
                    ))}
                  </div>
                  <div data-ui="inline-note" className={inlineNoteStyles}>
                    <Info size={18} />
                    <span>{BUDGET_DISCLAIMER}</span>
                  </div>
                </section>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
        <aside data-ui="result-aside" className="mobile:w-full">
          {weather && (
            <section
              data-ui="weather-card"
              className="p-[25px] rounded-[23px] bg-[#edf3fa] text-[#6d84a0] tablet:p-5 mobile:p-[21px]
                mobile:rounded-[20px] [&_>_strong]:block [&_>_strong]:text-[40px]
                [&_>_strong]:text-[#415975] [&_>_strong]:font-[650] [&_>_strong]:tracking-[-1.8px]
                tablet:[&_>_strong]:text-[32px] mobile:[&_>_strong]:text-[35px] [&_h3]:text-[12px]
                [&_h3]:mt-1.5 [&_h3]:font-[650] mobile:[&_h3]:text-[12px]
                mobile-type:[&_h3]:text-[12px] [&_>_p]:text-[11px] [&_>_p]:mt-[7px]
                [&_>_p]:text-[#91a3b9] mobile:[&_>_p]:text-[11px] mobile-type:[&_>_p]:text-[12px]
                [&_>_small]:block [&_>_small]:text-[11px] [&_>_small]:text-[#9bacbf]
                [&_>_small]:mt-3.5"
            >
              <div
                data-ui="weather-top"
                className="flex items-center justify-between mb-1.5 [&_>_span]:text-[11px]
                  [&_>_span]:tracking-[1.3px] [&_>_span]:font-[750] mobile:[&_>_span]:text-[11px]
                  [&_>_svg]:text-[#c6a86f]"
              >
                <span>ПОГОДА В ПОЕЗДКЕ</span>
                <CloudSun size={34} strokeWidth={1.5} />
              </div>
              <strong>
                {Math.round(weather.temperature_min_c)}…
                {Math.round(weather.temperature_max_c)}°
              </strong>
              <h3>{weather.description}</h3>
              <p>
                {dateLabel(weather.date)}
                {weather.precipitation_probability_percent != null &&
                  ` · осадки ${weather.precipitation_probability_percent}%`}
              </p>
              <div
                data-ui="weather-advice"
                className="[border-top:1px_solid_#dce6f3] mt-[19px] pt-[17px] text-[11px] leading-[1.8]
                  mobile:text-[11px] mobile:leading-[1.9] mobile-type:text-[14px]"
              >
                {plan.weather_advice}
              </div>
              <small>{plan.weather.provider}</small>
            </section>
          )}
          <div
            data-ui="travel-note"
            className="bg-[#f4f0e5] rounded-[22px] p-[25px] mt-5 mobile:hidden [&_h3]:text-[19px]
              [&_h3]:font-[750] [&_h3]:tracking-[-0.6px] [&_h3]:leading-[1.5] [&_h3]:text-[#7a7058]
              [&_h3]:mt-[7px] [&_h3]:mx-0 [&_h3]:mb-3 [&_p]:text-[11px] [&_p]:text-[#a5997b]
              [&_p]:leading-[1.9]"
          >
            <span data-ui="note-spark" className="text-[#ae9b68] text-[26px]">
              ✦
            </span>
            <h3>
              Оставьте место
              <br />
              для спонтанности
            </h3>
            <p>Лучшие моменты иногда случаются между пунктами плана.</p>
          </div>
        </aside>
      </div>
      <section
        data-ui="source-details"
        className="[border-top:1px_solid_var(--line)] mt-7 pt-2 px-[3px] pb-0 text-[#919cb1] text-[11px]
          mobile:text-[11px] mobile:mt-5.5 mobile-type:text-[12px] mobile-spacing:mt-6 [&_ul]:py-0
          [&_ul]:pr-0 [&_ul]:pl-5 [&_ul]:leading-[1.9] [&_li]:mb-[7px] [&_p]:text-[11px]
          [&_p]:leading-[1.8] mobile:[&_p]:text-[11px]"
      >
        <button
          data-ui="source-toggle"
          className={
            '[[data-ui~=source-details]_&]:flex [[data-ui~=source-details]_&]:items-center [[data-ui~=source-details]_&]:gap-2 [[data-ui~=source-details]_&]:cursor-pointer [[data-ui~=source-details]_&]:[list-style:none] [[data-ui~=source-details]_&]:text-[11px] [[data-ui~=source-details]_&]:font-[650] mobile:[[data-ui~=source-details]_&]:text-[11px] mobile-type:[[data-ui~=source-details]_&]:text-[12px] [[data-ui~=source-details]_&]:w-full [[data-ui~=source-details]_&]:min-h-11 [[data-ui~=source-details]_&]:p-0 [[data-ui~=source-details]_&]:bg-transparent [[data-ui~=source-details]_&]:text-[inherit] [[data-ui~=source-details]_&]:text-left [[data-ui~=source-details]_&_>_svg:last-child]:ml-auto [&_>_svg]:shrink-0 [&_>_svg:last-child]:[transition:transform_0.28s_ease] reduce-loading:[&_>_svg:last-child]:[transition:none] [&[aria-expanded="true"]_>_svg:last-child]:[transform:rotate(180deg)]'
          }
          type="button"
          aria-expanded={checksOpen}
          aria-controls="trip-checks"
          onClick={() => setChecksOpen((open) => !open)}
        >
          <Info size={17} /> Что стоит проверить <ChevronDown size={17} />
        </button>
        <motion.div
          id="trip-checks"
          data-ui="source-content"
          className="overflow-hidden"
          initial={false}
          animate={{
            height: checksOpen ? "auto" : 0,
            opacity: checksOpen ? 1 : 0,
          }}
          transition={{
            duration: reducedMotion ? 0 : 0.28,
            ease: "easeInOut",
          }}
          inert={!checksOpen}
          aria-hidden={!checksOpen}
        >
          <div
            data-ui="source-content-inner"
            className="pt-2 px-0 pb-1 [&_ul]:mt-0 [&_ul]:mx-0 [&_ul]:mb-3 [&_p]:m-0"
          >
            <ul>
              {tripNotices(plan).map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <p>
              Создано {new Date(plan.created_at).toLocaleString("ru-RU")}.
              Сведения могут измениться.
            </p>
          </div>
        </motion.div>
      </section>
      <div
        data-ui="result-sticky"
        className="fixed z-[20] bottom-4.5 left-[50%] [transform:translateX(-50%)] flex gap-[9px]
          bg-[#ffffffef] [backdrop-filter:blur(15px)] [border:1px_solid_var(--line)] rounded-[23px]
          p-[9px] [box-shadow:0_8px_30px_#3443710e] max-w-[calc(100%_-_24px)] w-106 mobile:left-0
          mobile:right-0 mobile:bottom-0 mobile:[transform:none] mobile:max-w-none mobile:w-full
          mobile:pt-3 mobile:px-6 mobile:pb-[calc(12px_+_env(safe-area-inset-bottom))]
          mobile:rounded-[20px_20px_0_0] mobile:[border-left:0] mobile:[border-right:0]
          mobile:[border-bottom:0] mobile:gap-[9px] mobile:[box-shadow:0_-4px_24px_#34437107]
          narrow:px-[17px] narrow-spacing:px-5 mobile:[&_svg]:size-[17px]"
      >
        <button
          id="copy-trip"
          data-ui="button secondary"
          className="min-h-13.5 inline-flex items-center justify-center gap-3 py-[15px] px-5.5 rounded-[17px]
            text-[14px] font-[750] no-underline [transition:background_0.18s,_box-shadow_0.18s]
            mobile:min-h-[53px] mobile:text-[13px] mobile:rounded-[15px] mobile-type:text-[14px]
            [[data-ui~=button]&]:bg-[#eff1fb] [[data-ui~=button]&]:text-brand
            [[data-ui~=result-sticky]_>_&]:text-[11px] [[data-ui~=result-sticky]_>_&]:p-[13px]
            [[data-ui~=result-sticky]_>_&]:gap-[7px] mobile:[[data-ui~=result-sticky]_>_&]:text-[11px]
            mobile:[[data-ui~=result-sticky]_>_&]:min-h-[51px]
            mobile:[[data-ui~=result-sticky]_>_&]:py-[13px]
            mobile:[[data-ui~=result-sticky]_>_&]:px-3.5
            mobile:[[data-ui~=result-sticky]_>_&]:rounded-[14px]
            narrow:[[data-ui~=result-sticky]_>_&]:text-[11px]
            mobile-type:[[data-ui~=result-sticky]_>_&]:text-[14px]
            narrow-type:[[data-ui~=result-sticky]_>_&]:[flex:0_0_51px]
            narrow-type:[[data-ui~=result-sticky]_>_&]:p-3
            narrow-type:[[data-ui~=result-sticky]_>_&_>_span]:hidden"
          onClick={copy}
        >
          <Copy size={18} />
          <span>Копировать</span>
        </button>
        <button
          id="share-trip"
          data-ui="button primary"
          className={primaryButtonStyles}
          onClick={prepareShare}
          disabled={sharing}
        >
          <Share2 size={18} />
          <span>{sharing ? "Готовим ссылку…" : "Позвать с собой"}</span>
        </button>
      </div>
    </div>
  );
}

function DestinationPhoto({
  photo,
  city,
}: {
  photo: NonNullable<TripPlan["destination_photo"]>;
  city: string;
}) {
  const [failed, setFailed] = useState(false);
  if (failed || !safeUrl(photo.url)) return null;
  return (
    <figure className="m-0 mb-6">
      <img
        src={safeUrl(photo.url)!}
        alt={`Вид города ${city}`}
        onError={() => setFailed(true)}
        className="block h-70 mobile:h-47.5 w-full rounded-3xl object-cover"
        referrerPolicy="no-referrer"
      />
    </figure>
  );
}
