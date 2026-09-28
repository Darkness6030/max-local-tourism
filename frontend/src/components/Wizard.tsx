import { nightsLabel } from "../lib";
import {
  wizardFieldLabelStyles,
  activeStyles,
  doneStyles,
  eyebrowStyles,
  fieldLabelStyles,
  iconButtonStyles,
  inlineNoteStyles,
  inputWithIconStyles,
  selectedChoiceStyles,
} from "../ui-styles";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import {
  ArrowLeft,
  Baby,
  CalendarDays,
  CarFront,
  Check,
  ChevronDown,
  Clock3,
  Coffee,
  Footprints,
  Heart,
  Landmark,
  MapPin,
  Mountain,
  Sparkles,
  TrainFront,
  Trees,
  Users,
  UserRound,
  Utensils,
  Wallet,
  X,
} from "lucide-react";
import type { AppConfig, Draft } from "../types";
import { addDays, dateLabel, money, validateStep, api } from "../lib";
import { Choice, Counter, Notice, Primary } from "./UI";

export const stepNames = [
  "Направление",
  "Даты",
  "Компания",
  "Интересы",
  "Детали",
];
const headings = [
  [
    "Куда зовёт дорога?",
    "Выберите знакомое место или доверьтесь маленькой спонтанности.",
  ],
  [
    "Когда устроим побег?",
    "Один насыщенный день или целые выходные — решать вам.",
  ],
  [
    "С кем разделим впечатления?",
    "Подберём занятия и посчитаем бюджет для вашей компании.",
  ],
  [
    "Что делает день вашим?",
    "Можно выбрать несколько вариантов. Чем больше знаем, тем лучше маршрут.",
  ],
  ["Последние штрихи", "Настроим бюджет и дорогу. Дальше — приятная часть."],
];
const interests = [
  ["Природа", Trees, "Леса и тишина"],
  ["История", Landmark, "Города с историями"],
  ["Местная кухня", Utensils, "Попробовать новое"],
  ["Прогулки", Footprints, "Красивые улочки"],
  ["Активный отдых", Mountain, "Больше движения"],
  ["Музеи", Coffee, "Искусство и открытия"],
] as const;


const durationCardStyles = `
  [border:1.5px_solid_#e9ecf3] bg-white rounded-[17px] py-5 px-1.5 flex items-center flex-col
  mobile:py-5 mobile:px-1.5 mobile:min-h-33.5 [&_>_span]:text-[27px] [&_>_span]:text-[#a0aec7]
  [&_>_span]:leading-[1.4] [&_>_span]:mb-[9px] mobile:[&_>_span]:text-[28px] [&_strong]:text-[12px]
  [&_strong]:font-[750] mobile:[&_strong]:text-[12px] [&_small]:text-[11px] [&_small]:text-[#a0a6b6]
  [&_small]:mt-[5px] mobile:[&_small]:text-[11px]
`;

export function Wizard({
  draft,
  initData,
  update,
  config,
  step,
  setStep,
  onExit,
  onSubmit,
  busy,
  serverError,
}: {
  draft: Draft;
  initData: string;
  update: (patch: Partial<Draft>) => void;
  config: AppConfig;
  step: number;
  setStep: (step: number) => void;
  onExit: () => void;
  onSubmit: () => void;
  busy: boolean;
  serverError: string;
}) {
  const [error, setError] = useState<string | null>(null);
  const [cityError, setCityError] = useState<string | null>(null);
  const [checkingCity, setCheckingCity] = useState(false);
  const cityRequest = useRef<AbortController | null>(null);
  useEffect(() => {
    cityRequest.current?.abort();
    cityRequest.current = null;
    setCheckingCity(false);
    setError(null);
    setCityError(null);
    return () => cityRequest.current?.abort();
  }, [draft.origin, draft.destination, draft.destinationMode]);
  const headingRef = useRef<HTMLHeadingElement>(null);
  useLayoutEffect(() => {
    setError(null);
    setCityError(null);
    window.scrollTo({ top: 0, behavior: "instant" });
    headingRef.current?.focus({ preventScroll: true });
  }, [step]);
  const move = (next: number) => {
    setStep(next);
  };
  const next = async () => {
    if (cityRequest.current) return;
    const problem = validateStep(step, draft, config);
    if (problem) {
      if (step === 0 && draft.destinationMode === "manual")
        setCityError(problem);
      else setError(problem);
      return;
    }
    if (step === 0 && draft.destinationMode === "manual") {
      const controller = new AbortController();
      cityRequest.current = controller;
      setCheckingCity(true);
      setError(null);
      setCityError(null);
      try {
        const query = new URLSearchParams({
          origin: draft.origin,
          destination: draft.destination!.trim(),
        });
        await api(`/cities/validate?${query}`, initData, {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
      } catch (cause) {
        if (!controller.signal.aborted) setCityError((cause as Error).message);
        return;
      } finally {
        if (cityRequest.current === controller) {
          cityRequest.current = null;
          setCheckingCity(false);
        }
      }
    }
    if (step < 4) move(step + 1);
    else {
      for (let index = 0; index < 5; index++) {
        if (validateStep(index, draft, config)) {
          move(index);
          return;
        }
      }
      onSubmit();
    }
  };
  const maxStart = addDays(config.last_trip_date, 1 - draft.days);
  const saturday = (() => {
    const day = new Date(`${config.today}T12:00:00Z`).getUTCDay();
    return addDays(config.today, (6 - day + 7) % 7);
  })();
  return (
    <div
      data-ui="wizard-layout"
      className="grid grid-cols-[1fr_1.25fr] gap-12 max-w-237.5 my-0 mx-auto desktop-fit:gap-[45px]
        tablet:gap-[35px] tablet:grid-cols-[0.8fr_1.2fr] mobile:block mobile:m-0"
    >
      <aside
        data-ui="wizard-aside"
        className="py-8 px-0 mobile:hidden short:pt-5 [&_h2]:text-[36px] [&_h2]:leading-[1.23]
          [&_h2]:tracking-[-1.5px] [&_h2]:mt-5 [&_h2]:mx-0 [&_h2]:mb-4 [&_h2]:font-extrabold
          tablet:[&_h2]:text-[31px] short:[&_h2]:text-[30px] short:[&_h2]:my-4 short:[&_h2]:mx-0
          [&_h2_span]:text-brand [&_>_p]:max-w-[285px] [&_>_p]:text-[13px] [&_>_p]:text-muted
          [&_>_p]:leading-[1.9] [&_ol]:[list-style:none] [&_ol]:p-0 [&_ol]:my-9 [&_ol]:mx-0
          [&_ol]:grid [&_ol]:gap-5.5 short:[&_ol]:my-6 short:[&_ol]:mx-0 short:[&_ol]:gap-4
          [&_li]:flex [&_li]:items-center [&_li]:gap-3.5 [&_li]:text-[#a2a7b6] [&_li]:text-[12px]
          [&_li_>_span]:size-[31px] [&_li_>_span]:[border:1px_solid_#e0e4ee]
          [&_li_>_span]:rounded-[50%] [&_li_>_span]:grid [&_li_>_span]:place-items-center
          [&_li_>_span]:text-[11px]"
      >
        <span data-ui="eyebrow" className={eyebrowStyles}>
          ПУТЕШЕСТВИЕ НАЧИНАЕТСЯ
        </span>
        <h2>
          Хороший план.
          <br />
          <span>Ваш выходной.</span>
        </h2>
        <p>Пять простых шагов — и можно предвкушать поездку.</p>
        <ol>
          {stepNames.map((name, i) => (
            <li
              key={name}
              data-ui={step === i ? "active" : step > i ? "done" : ""}
              className={step === i ? activeStyles : step > i ? doneStyles : ""}
            >
              <span>{step > i ? <Check size={16} /> : `0${i + 1}`}</span>
              {name}
            </li>
          ))}
        </ol>
        <div
          data-ui="aside-note"
          className="flex gap-2.5 items-center text-[11px] text-[#828baa] leading-[1.8]"
        >
          <Sparkles size={18} />
          <span>
            Подстроимся под погоду,
            <br />
            бюджет и ваше настроение.
          </span>
        </div>
      </aside>
      <div
        data-ui="wizard"
        className="bg-white [border:1px_solid_var(--line)] rounded-[28px] overflow-hidden mobile:bg-[#f8f9fc]
          mobile:[border:0] mobile:rounded-none mobile:min-h-[100dvh] mobile:overflow-visible
          short:overflow-clip"
      >
        <header
          data-ui="wizard-top"
          className="flex justify-between items-center h-[73px] py-0 px-[17px]
            mobile:pt-[env(safe-area-inset-top)] mobile:px-3.5 mobile:pb-0 mobile:h-[73px] short:h-15
            [&_>_span]:flex [&_>_span]:gap-3 [&_>_span]:text-[11px] [&_>_span]:font-bold
            [&_>_span]:text-muted mobile:[&_>_span]:text-[11px] [&_b]:text-brand
            [&_b_span]:text-[#b0b5c3] [&_b_span]:font-medium"
        >
          <button
            data-ui="icon-button"
            className={iconButtonStyles}
            aria-label={step ? "Предыдущий шаг" : "На главную"}
            onClick={() => (step ? move(step - 1) : onExit())}
          >
            <ArrowLeft size={21} />
          </button>
          <span>
            {stepNames[step]}{" "}
            <b>
              {step + 1}
              <span> / 5</span>
            </b>
          </span>
          <button
            data-ui="icon-button"
            className={iconButtonStyles}
            aria-label="Закрыть анкету"
            onClick={onExit}
          >
            <X size={20} />
          </button>
        </header>
        <div
          data-ui="step-progress"
          className="flex gap-[5px] py-0 px-7 mobile:py-0 mobile:px-6 mobile:gap-1.5 narrow-spacing:px-5
            [&_>_span]:h-1 [&_>_span]:flex-1 [&_>_span]:rounded-[3px] [&_>_span]:bg-[#edf0f7]
            [&_>_span]:[transition:background_0.25s] mobile:[&_>_span]:h-1"
          aria-label={`Шаг ${step + 1} из 5`}
        >
          {stepNames.map((_, i) => (
            <span
              key={i}
              data-ui={i <= step ? "active" : ""}
              className={i <= step ? activeStyles : ""}
            />
          ))}
        </div>
        <form
          id="trip-form"
          onSubmit={(event) => {
            event.preventDefault();
            void next();
          }}
        >
            <motion.div
              key={step}
              data-ui="step-content"
              className="pt-6 px-6 pb-4 tablet:px-6 mobile:pt-6 mobile:px-6 mobile:pb-4 narrow:px-[21px]
                narrow-spacing:px-5 short:pt-5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.12 }}
            >
              <div
                data-ui="step-heading"
                className="mb-6 mobile:mb-6 mobile-spacing:mb-6 short:mb-5 [&_h1]:text-[29px]
                  [&_h1]:tracking-[-1.2px] [&_h1]:leading-[1.27] [&_h1]:mt-[11px] [&_h1]:mx-0
                  [&_h1]:mb-3 [&_h1]:font-extrabold tablet:[&_h1]:text-[26px]
                  mobile:[&_h1]:text-[29px] mobile:[&_h1]:leading-[1.27]
                  mobile:[&_h1]:tracking-[-1.2px] mobile:[&_h1]:mt-2.5 mobile:[&_h1]:mx-0
                  mobile:[&_h1]:mb-[13px] mobile:[&_h1]:max-w-[325px] narrow:[&_h1]:text-[27px]
                  mobile-spacing:[&_h1]:mt-2 mobile-spacing:[&_h1]:mx-0 mobile-spacing:[&_h1]:mb-3
                  [&_>_p]:text-muted [&_>_p]:text-[12px] [&_>_p]:leading-[1.85] [&_>_p]:max-w-85
                  mobile:[&_>_p]:text-[11px] mobile:[&_>_p]:leading-[1.85] mobile:[&_>_p]:max-w-77.5
                  mobile-type:[&_p]:text-[14px] mobile-type:[&_p]:leading-[1.8] [&_p]:text-[#687389]"
              >
                <span data-ui="eyebrow" className={eyebrowStyles}>
                  ШАГ 0{step + 1}
                </span>
                <h1 ref={headingRef} tabIndex={-1}>
                  {headings[step][0]}
                </h1>
                <p>{headings[step][1]}</p>
              </div>
              {step === 0 && (
                <>
                  <label
                    data-ui="field-label"
                    className={fieldLabelStyles}
                    htmlFor="origin"
                  >
                    Город отправления
                  </label>
                  <div
                    data-ui="input-with-icon"
                    className={inputWithIconStyles}
                  >
                    <MapPin size={19} />
                    <select
                      id="origin"
                      name="origin"
                      value={draft.origin}
                      onChange={(event) =>
                        update({ origin: event.target.value })
                      }
                    >
                      {config.origins.map((origin) => (
                        <option key={origin}>{origin}</option>
                      ))}
                    </select>
                  </div>
                  <span
                    data-ui="field-label spaced"
                    className={wizardFieldLabelStyles}
                  >
                    А куда хочется?
                  </span>
                  <div
                    data-ui="choice-stack"
                    className="grid gap-[11px] mt-[11px] mobile:gap-3"
                  >
                    <Choice
                      selected={draft.destinationMode === "ai"}
                      onClick={() => update({ destinationMode: "ai" })}
                      icon={<Sparkles size={23} />}
                      title="Удивите меня"
                      subtitle="Подберём город под ваши интересы"
                    />
                    <Choice
                      selected={draft.destinationMode === "manual"}
                      onClick={() => update({ destinationMode: "manual" })}
                      icon={<MapPin size={23} />}
                      title="Уже знаю куда"
                      subtitle="Есть место, о котором давно думаю"
                    />
                  </div>
                  {draft.destinationMode === "manual" && (
                    <label
                      data-ui="field-label spaced"
                      className="block mt-6 text-[13px] font-semibold leading-[20px]"
                    >
                      Город назначения
                      <input
                        autoFocus
                        name="destination"
                        className="mt-[9px] block h-13.5 w-full rounded-[13px] border border-solid
                          border-[#e6e9f0] bg-white px-3.5 py-0 text-[13px] mobile:text-[16px]
                          font-medium leading-[20px] text-ink placeholder:text-[length:inherit]
                          placeholder:leading-[20px] placeholder:text-[#a3a9b8]
                          placeholder:opacity-100 aria-invalid:border-[#d86868]
                          aria-invalid:bg-[#fff8f8] aria-invalid:focus:[outline-color:#d86868]"
                        aria-describedby={
                          cityError ? "destination-help" : undefined
                        }
                        aria-invalid={Boolean(cityError)}
                        placeholder="Например, Коломна"
                        maxLength={160}
                        value={draft.destination || ""}
                        onChange={(event) =>
                          update({ destination: event.target.value })
                        }
                      />
                      {cityError && (
                        <span
                          id="destination-help"
                          role="alert"
                          className="mt-2 block text-[11px] font-medium leading-[1.6] text-[#b94444]"
                        >
                          {cityError}
                        </span>
                      )}
                    </label>
                  )}
                  <div data-ui="inline-note" className={inlineNoteStyles}>
                    <MapPin size={16} />
                    <span>
                      Доступные города отправления — в списке выше.
                      <br />
                      Впереди — ещё больше отправных точек.
                    </span>
                  </div>
                </>
              )}
              {step === 1 && (
                <>
                  <label
                    data-ui="field-label"
                    className={fieldLabelStyles}
                    htmlFor="start-date"
                  >
                    День отправления
                  </label>
                  <div
                    data-ui="input-with-icon date-input"
                    className={inputWithIconStyles}
                  >
                    <CalendarDays size={20} />
                    <input
                      id="start-date"
                      name="start_date"
                      type="date"
                      required
                      min={config.today}
                      max={maxStart}
                      value={draft.start_date}
                      onChange={(event) =>
                        update({ start_date: event.target.value })
                      }
                    />
                  </div>
                  <div
                    data-ui="quick-chips"
                    className="flex flex-wrap gap-[7px] mt-[11px] [&_button]:[border:1px_solid_#e8ebf3]
                      [&_button]:rounded-[11px] [&_button]:bg-white [&_button]:text-[#8a92a3]
                      [&_button]:py-[7px] [&_button]:px-3.5 [&_button]:text-[11px]
                      [&_button]:min-h-9.5 mobile:[&_button]:text-[11px] mobile:[&_button]:min-h-10
                      mobile:[&_button]:py-2 mobile:[&_button]:px-3.5 mobile:[&_button]:bg-white"
                  >
                    {[
                      ["Завтра", config.default_date],
                      ["В субботу", saturday],
                    ].map(([label, date]) => (
                      <button
                        type="button"
                        key={label}
                        disabled={date > maxStart}
                        data-ui={draft.start_date === date ? "active" : ""}
                        className={
                          draft.start_date === date ? activeStyles : ""
                        }
                        onClick={() => update({ start_date: date })}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <span
                    data-ui="field-label spaced"
                    className={wizardFieldLabelStyles}
                  >
                    Сколько у нас времени?
                  </span>
                  <div
                    data-ui="duration-grid"
                    className="grid grid-cols-[repeat(3,_1fr)] gap-[9px] mt-3 mobile:gap-2.5"
                  >
                    {[1, 2, 3].map((days) => (
                      <button
                        type="button"
                        key={days}
                        aria-pressed={draft.days === days}
                        data-ui={`duration-card ${draft.days === days ? "selected" : ""}`}
                        className={`${durationCardStyles} ${draft.days === days ? selectedChoiceStyles : ""}`}
                        onClick={() => {
                          const last = addDays(config.last_trip_date, 1 - days);
                          update({
                            days,
                            start_date:
                              draft.start_date > last ? last : draft.start_date,
                          });
                        }}
                      >
                        <span>{days === 1 ? "☀" : days === 2 ? "◒" : "✦"}</span>
                        <strong>
                          {days} {days === 1 ? "день" : "дня"}
                        </strong>
                        <small>
                          {days === 1
                            ? "Мини-побег"
                            : days === 2
                              ? "Выходные"
                              : "Мини-отпуск"}
                        </small>
                      </button>
                    ))}
                  </div>
                  <div
                    data-ui="trip-date-preview"
                    className="mt-[27px] rounded-[15px] bg-[#f6f7fc] p-4.5 flex gap-[13px] items-center
                      text-[#919fbe] mobile:bg-[#eef2fb] mobile:p-[17px] mobile:mt-4
                      [&_strong]:text-[12px] [&_strong]:block [&_strong]:text-[#59647e]
                      mobile:[&_strong]:text-[12px] [&_span]:text-[11px] [&_span]:block
                      [&_span]:mt-[5px] [&_span]:text-[#929caf] mobile:[&_span]:text-[11px]"
                  >
                    <CalendarDays size={22} />
                    <div>
                      <strong>
                        {dateLabel(draft.start_date)}
                        {draft.days > 1
                          ? ` — ${dateLabel(addDays(draft.start_date, draft.days - 1))}`
                          : ""}
                      </strong>
                      <span>
                        {draft.days === 1
                          ? "Уедем и вернёмся в один день"
                          : `${nightsLabel(draft.days - 1)} в новом месте`}
                      </span>
                    </div>
                  </div>
                  <p
                    data-ui="field-hint"
                    className="text-[11px] leading-[1.85] text-[#99a0b2] mt-3 mobile:text-[11px]
                      mobile-type:text-[12px]"
                  >
                    Даты доступны до {dateLabel(config.last_trip_date)} — чтобы
                    учесть актуальный прогноз.
                  </p>
                </>
              )}
              {step === 2 && (
                <>
                  <div
                    data-ui="group-grid"
                    className="grid grid-cols-[1fr_1fr] gap-[11px]"
                  >
                    {(
                      [
                        {
                          value: "solo",
                          title: "Наедине с собой",
                          subtitle: "В своём ритме",
                          icon: UserRound,
                        },
                        {
                          value: "couple",
                          title: "Вдвоём",
                          subtitle: "Общие открытия",
                          icon: Heart,
                        },
                        {
                          value: "friends",
                          title: "С друзьями",
                          subtitle: "Будет что вспомнить",
                          icon: Users,
                        },
                        {
                          value: "family",
                          title: "С семьёй",
                          subtitle: "Всем по душе",
                          icon: Baby,
                        },
                      ] as const
                    ).map((item) => (
                      <Choice
                        key={item.value}
                        selected={draft.group_type === item.value}
                        onClick={() =>
                          update({
                            group_type: item.value,
                            travelers:
                              item.value === "solo"
                                ? 1
                                : item.value === "couple"
                                  ? 2
                                  : Math.max(draft.travelers, 2),
                          })
                        }
                        icon={<item.icon size={24} />}
                        title={item.title}
                        subtitle={item.subtitle}
                      />
                    ))}
                  </div>
                  <div
                    data-ui="counter-row"
                    className="flex justify-between items-center my-6.5 mx-0 mobile:py-[5px] mobile:px-0
                      [&_strong]:text-[12px] [&_p]:text-[11px] [&_p]:text-muted [&_p]:mt-[5px]"
                  >
                    <div>
                      <strong>Сколько нас?</strong>
                      <p>Всего, включая детей</p>
                    </div>
                    <Counter
                      value={draft.travelers}
                      onChange={(travelers) => update({ travelers })}
                      label="Число путешественников"
                    />
                  </div>
                  {draft.group_type === "family" && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <label data-ui="field-label" className={fieldLabelStyles}>
                        Возраст детей
                        <input
                          name="children_ages"
                          placeholder="Например: 5, 12"
                          value={draft.childrenText}
                          onChange={(event) =>
                            update({ childrenText: event.target.value })
                          }
                          inputMode="numeric"
                        />
                      </label>
                      <p
                        data-ui="field-hint"
                        className="text-[11px] leading-[1.85] text-[#99a0b2] mt-3 mobile:text-[11px]
                          mobile-type:text-[12px]"
                      >
                        Через запятую. Если едут только взрослые, оставьте
                        пустым.
                      </p>
                    </motion.div>
                  )}
                </>
              )}
              {step === 3 && (
                <>
                  <div
                    data-ui="interests-grid"
                    className="grid grid-cols-[1fr_1fr] gap-[11px] mobile:gap-2.5"
                  >
                    {interests.map(([name, Icon, hint]) => (
                      <Choice
                        key={name}
                        selected={draft.interests.includes(name)}
                        onClick={() =>
                          update({
                            interests: draft.interests.includes(name)
                              ? draft.interests.filter((item) => item !== name)
                              : [...draft.interests, name],
                          })
                        }
                        icon={<Icon size={25} />}
                        title={name}
                        subtitle={hint}
                      />
                    ))}
                  </div>
                  <label
                    data-ui="field-label spaced"
                    className={wizardFieldLabelStyles}
                  >
                    Есть особые пожелания?
                    <span
                      data-ui="optional"
                      className="[[data-ui~=field-label]_&]:font-medium
                        [[data-ui~=field-label]_&]:text-[#a0a7b8]
                        [[data-ui~=field-label]_&]:text-[11px]
                        [[data-ui~=field-label]_&]:[float:right]
                        mobile:[[data-ui~=field-label]_&]:text-[11px]"
                    >
                      Необязательно
                    </span>
                    <textarea
                      name="preferences"
                      placeholder="Без раннего подъёма, побольше кофе, поменьше музеев…"
                      value={draft.preferences}
                      onChange={(event) =>
                        update({ preferences: event.target.value })
                      }
                      maxLength={1200}
                      rows={3}
                    />
                  </label>
                  <span
                    data-ui="field-label spaced"
                    className={wizardFieldLabelStyles}
                  >
                    В каком темпе?
                  </span>
                  <div
                    data-ui="segmented"
                    className="flex gap-1 p-[5px] bg-[#f2f4f9] rounded-[14px] mt-2.5 mobile:bg-[#eaf0f9]
                      [&_button]:flex-1 [&_button]:[background:none] [&_button]:text-[11px]
                      [&_button]:text-[#9299ab] [&_button]:rounded-[10px] [&_button]:min-h-[39px]
                      [&_button]:p-[7px] mobile:[&_button]:text-[11px] mobile:[&_button]:min-h-10.5"
                  >
                    {(
                      [
                        ["relaxed", "Не спеша"],
                        ["balanced", "В меру"],
                        ["intensive", "Всё успеть"],
                      ] as const
                    ).map(([value, label]) => (
                      <button
                        key={value}
                        type="button"
                        aria-pressed={draft.pace === value}
                        data-ui={draft.pace === value ? "active" : ""}
                        className={draft.pace === value ? activeStyles : ""}
                        onClick={() => update({ pace: value })}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </>
              )}
              {step === 4 && (
                <>
                  <div
                    data-ui="budget-input"
                    className="py-6 px-5 bg-[#f5f7ff] rounded-[20px] text-center mobile:bg-[#eef2ff]
                      mobile:py-6 mobile:px-[15px] [&_label]:text-[11px] [&_label]:text-[#8b95af]
                      mobile:[&_label]:text-[11px] [&_>_div]:flex [&_>_div]:justify-center
                      [&_>_div]:items-center [&_>_div]:mt-3 [&_>_div]:mx-0 [&_>_div]:mb-2
                      [&_>_div]:gap-1 [&_input]:[appearance:textfield]
                      [&_input]:[-moz-appearance:textfield] [&_input]:[background:none]
                      [&_input]:[border:0] [&_input]:[outline:none] [&_input]:text-[37px]
                      [&_input]:tracking-[-1.5px] [&_input]:text-right [&_input]:font-extrabold
                      [&_input]:w-[155px] [&_input]:text-ink [&_input]:p-0 [&_input]:min-h-12
                      mobile:[&_input]:text-[39px] mobile:[&_input]:w-40.5
                      [&_input::-webkit-inner-spin-button]:[-webkit-appearance:none]
                      [&_input::-webkit-inner-spin-button]:m-0
                      [&_input::-webkit-outer-spin-button]:[-webkit-appearance:none]
                      [&_input::-webkit-outer-spin-button]:m-0 [&_>_div_>_span]:text-[31px]
                      [&_>_div_>_span]:text-[#98a5c9] [&_small]:text-[11px] [&_small]:text-[#99a2b7]
                      mobile:[&_small]:text-[11px]"
                  >
                    <label htmlFor="budget">Бюджет на всю компанию</label>
                    <div>
                      <input
                        id="budget"
                        name="budget_rub"
                        type="number"
                        min={1000}
                        max={1000000}
                        step={100}
                        required
                        value={draft.budget_rub || ""}
                        onChange={(event) =>
                          update({ budget_rub: Number(event.target.value) })
                        }
                        inputMode="numeric"
                      />
                      <span>₽</span>
                    </div>
                    <small>
                      Примерно{" "}
                      {money(Math.round(draft.budget_rub / draft.travelers))} на
                      человека
                    </small>
                  </div>
                  <div
                    data-ui="quick-chips budget-chips"
                    className="flex flex-wrap gap-[7px] mt-[11px] [&_button]:[border:1px_solid_#e8ebf3]
                      [&_button]:rounded-[11px] [&_button]:bg-white [&_button]:text-[#8a92a3]
                      [&_button]:py-[7px] [&_button]:px-3.5 [&_button]:text-[11px]
                      [&_button]:min-h-9.5 mobile:[&_button]:text-[11px] mobile:[&_button]:min-h-10
                      mobile:[&_button]:py-2 mobile:[&_button]:px-3.5 mobile:[&_button]:bg-white
                      [[data-ui~=quick-chips]&]:justify-center [[data-ui~=quick-chips]&]:gap-1.5
                      mobile:[[data-ui~=quick-chips]&]:flex-nowrap
                      mobile:[[data-ui~=quick-chips]&]:gap-1.5
                      mobile-type:[[data-ui~=quick-chips]&]:flex-wrap
                      [[data-ui~=quick-chips]&_button]:py-2 [[data-ui~=quick-chips]&_button]:px-[11px]
                      [[data-ui~=quick-chips]&_button]:text-[11px]
                      mobile:[[data-ui~=quick-chips]&_button]:py-[9px]
                      mobile:[[data-ui~=quick-chips]&_button]:px-1.5
                      mobile:[[data-ui~=quick-chips]&_button]:flex-1
                      mobile:[[data-ui~=quick-chips]&_button]:text-[11px]
                      mobile:[[data-ui~=quick-chips]&_button]:whitespace-nowrap
                      narrow:[[data-ui~=quick-chips]&_button]:text-[11px]"
                  >
                    {[5000, 12000, 20000, 30000].map((amount) => (
                      <button
                        type="button"
                        key={amount}
                        data-ui={draft.budget_rub === amount ? "active" : ""}
                        className={
                          draft.budget_rub === amount ? activeStyles : ""
                        }
                        onClick={() => update({ budget_rub: amount })}
                      >
                        {money(amount)}
                      </button>
                    ))}
                  </div>
                  <span
                    data-ui="field-label spaced"
                    className={wizardFieldLabelStyles}
                  >
                    Как добираемся?
                  </span>
                  <div
                    data-ui="transport-choices"
                    className="grid grid-cols-[1fr_1fr] gap-2.5 mt-[11px]"
                  >
                    <Choice
                      selected={!draft.has_car}
                      onClick={() => update({ has_car: false, preferred_transport: draft.preferred_transport === "bus" ? "bus" : "suburban" })}
                      icon={<TrainFront size={24} />}
                      title="Транспорт"
                      subtitle="Поезда и автобусы"
                    />
                    <Choice
                      selected={draft.has_car}
                      onClick={() => update({ has_car: true, preferred_transport: "car" })}
                      icon={<CarFront size={24} />}
                      title="На машине"
                      subtitle="За рулём сами"
                    />
                  </div>
                  <details
                    data-ui="travel-options"
                    className="[border-top:1px_solid_var(--line)] [border-bottom:1px_solid_var(--line)] mt-6
                      pb-0 [&[open]]:pb-[17px] [&_summary]:cursor-pointer [&_summary]:flex
                      [&_summary]:items-center [&_summary]:gap-2 [&_summary]:text-[11px]
                      [&_summary]:font-[650] [&_summary]:py-[17px] [&_summary]:px-0
                      [&_summary]:[list-style:none] mobile:[&_summary]:text-[11px]
                      [&_summary::-webkit-details-marker]:hidden [&_summary_>_span]:ml-auto
                      [&_summary_>_span]:text-[#939db0] [&_summary_>_span]:text-[11px]
                      [&_summary_>_span]:font-medium mobile:[&_summary_>_span]:text-[11px]"
                  >
                    <summary>
                      <Clock3 size={18} /> Время в дороге <span>Настроить</span>
                    </summary>
                    <div
                      data-ui="fields-pair"
                      className="grid grid-cols-2 gap-3 [&_>_label]:min-w-0 mobile:[&_input]:min-w-0
                        mobile:[&_input]:text-[16px]"
                    >
                      <label data-ui="field-label" className={fieldLabelStyles}>
                        Выезд не раньше
                        <span data-ui="time-input">
                          <input
                            name="departure_after"
                            type="time"
                            required
                            value={draft.departure_after}
                            onChange={(event) =>
                              update({ departure_after: event.target.value })
                            }
                          />
                        </span>
                      </label>
                      <label data-ui="field-label" className={fieldLabelStyles}>
                        Обратно не раньше
                        <span data-ui="time-input">
                          <input
                            name="return_after"
                            type="time"
                            required
                            value={draft.return_after}
                            onChange={(event) =>
                              update({ return_after: event.target.value })
                            }
                          />
                        </span>
                      </label>
                    </div>
                    <label
                      data-ui="field-label spaced"
                      className={`${wizardFieldLabelStyles} relative`}
                    >
                      Дорога в одну сторону
                      <select
                        className="appearance-none !pr-9"
                        name="max_travel_minutes"
                        value={draft.max_travel_minutes}
                        onChange={(event) =>
                          update({
                            max_travel_minutes: Number(event.target.value),
                          })
                        }
                      >
                        <option value={120}>До 2 часов</option>
                        <option value={240}>До 4 часов</option>
                        <option value={360}>До 6 часов</option>
                      </select>
                      <ChevronDown size={18} aria-hidden="true" className="absolute right-3.5 bottom-[17px] pointer-events-none text-muted" />
                    </label>
                  </details>
                  <div data-ui="inline-note" className={inlineNoteStyles}>
                    <Wallet size={18} />
                    <span>
                      Цены в программе будут приблизительными. Бронировать и
                      оплачивать здесь ничего не нужно.
                    </span>
                  </div>
                </>
              )}
            </motion.div>
          <div
            data-ui="wizard-actions"
            className="py-4 px-6 [border-top:1px_solid_#f0f2f7] bg-white tablet:px-6 mobile:sticky
              mobile:bottom-0 mobile:pt-3 mobile:px-6
              mobile:pb-[max(12px,_var(--app-safe-bottom))]
              mobile:[border-top:1px_solid_#e9edf6] mobile:bg-[#f8f9fcf5]
              mobile:[backdrop-filter:blur(16px)] mobile:z-[15] narrow:px-[21px] narrow-spacing:px-5
              short:sticky short:bottom-0 short:z-[15] short:pt-3
              short:pb-[max(12px,_var(--app-safe-bottom))]"
          >
            {(error || serverError) && (
              <Notice error>{error || serverError}</Notice>
            )}
            <Primary
              type="submit"
              id={step === 4 ? "generate" : "next-step"}
              busy={busy || checkingCity}
            >
              {checkingCity
                ? "Проверяем город…"
                : step === 4
                  ? "Собрать мою поездку"
                  : "Продолжить"}
            </Primary>
            <span
              data-ui="action-caption"
              className="block text-center text-[11px] text-[#a1a7b6] mt-[11px] leading-[1.7]
                mobile:text-[11px] mobile:mt-2.5 mobile-type:text-[10px]"
            >
              {step === 4
                ? "ИИ соберёт программу, сервисы проверят погоду и дорогу"
                : "Можно вернуться и изменить любой ответ"}
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}
