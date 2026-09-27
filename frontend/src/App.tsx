import {
  activeStyles,
  appHeaderStyles,
  appMainStyles,
  avatarStyles,
  doneStyles,
  emptyStateStyles,
  eyebrowStyles,
  sectionHeadingStyles,
  softBlueIconStyles,
  textButtonStyles,
  tripsPageStyles,
} from "./ui-styles";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronRight,
  CloudSun,
  Coffee,
  Compass,
  Heart,
  House,
  MapPin,
  Navigation,
  Route,
  Sparkles,
  TrainFront,
} from "lucide-react";
import {
  api,
  addDays,
  ApiError,
  readStorage,
  restoreDraft,
  toRequest,
  writeStorage,
} from "./lib";
import type {
  AppConfig,
  Draft,
  Identity,
  Job,
  Screen,
  TripPlan,
  UserProfile,
} from "./types";
import { ProfileAvatar } from "./components/ProfileAvatar";
import { Profile } from "./components/Profile";
import { Brand, Notice, Primary } from "./components/UI";
import { Onboarding } from "./components/Onboarding";
import { Wizard } from "./components/Wizard";
import { MyTrips } from "./components/MyTrips";
import { MaxEntry } from "./components/MaxEntry";
import { TripResult } from "./components/TripResult";
import { PresetCards, PresetDetail } from "./components/Presets";
import type { TripPreset } from "./presets";
import { useMobileViewport } from "./useMobileViewport";
import journey from "./assets/journey.webp";
import journeySpb from "./assets/journey-spb.webp";

const ABOUT_FEATURES = [
  {
    Icon: Sparkles,
    title: "Программа с вашим характером",
    text: "ИИ предлагает занятия и оценивает расходы. Часы работы мест и цены нужно проверить.",
  },
  {
    Icon: CloudSun,
    title: "С оглядкой на погоду",
    text: "Прогноз получаем из погодного сервиса на выбранные даты.",
  },
  {
    Icon: TrainFront,
    title: "Дорога из реальных расписаний",
    text: "Показываем рейсы Яндекса и ссылки на карты. Билеты здесь не продаются.",
  },
];

const rawLaunch = () => {
  if (window.WebApp?.initData) return window.WebApp.initData;
  const params = new URLSearchParams(location.hash.slice(1)).getAll(
    "WebAppData",
  );
  return params.length === 1
    ? params[0]
    : params.length > 1
      ? "invalid-duplicate-launch-data"
      : "";
};

const sharedLaunch = () => {
  const value = window.WebApp?.initDataUnsafe?.start_param
    || new URLSearchParams(rawLaunch()).get("start_param")
    || new URLSearchParams(location.search).get("WebAppStartParam")
    || new URLSearchParams(location.hash.slice(1)).get("WebAppStartParam");
  return typeof value === "string" && /^trip_[a-f0-9]{32}$/.test(value)
    ? value.slice(5) : null;
};

export default function App() {
  useMobileViewport();
  const reducedMotion = useReducedMotion();
  const [onboarded, setOnboarded] = useState(true);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [onboardingBusy, setOnboardingBusy] = useState(false);
  const [onboardingError, setOnboardingError] = useState("");
  const onboardingLock = useRef(false);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [screen, setScreen] = useState<Screen>("home");
  const profileReturn = useRef<Screen>("home");
  const [homeRevision, setHomeRevision] = useState(0);
  const [preset, setPreset] = useState<TripPreset | null>(null);
  const [welcomeEntry, setWelcomeEntry] = useState(false);
  const [step, setStep] = useState(0);
  const [trip, setTrip] = useState<{ plan: TripPlan } | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [pollError, setPollError] = useState("");
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const [bootRetry, setBootRetry] = useState(0);
  const [booting, setBooting] = useState(true);
  const initData = useRef(rawLaunch());
  const prefix = useRef("");
  const pendingShare = useRef(sharedLaunch());
  const submitLock = useRef(false);
  useLayoutEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [screen, onboarded, homeRevision]);
  const navigate = useCallback((next: Screen) => {
    setWelcomeEntry(false);
    setScreen(next);
  }, []);
  const update = (patch: Partial<Draft>) => {
    setDraft((old) => (old ? { ...old, ...patch } : old));
    setSubmitError("");
  };
  const openProfile = () => {
    if (screen !== "profile") profileReturn.current = screen;
    navigate("profile");
  };
  const changeOrigin = (origin: string) => {
    if (!draft || !config?.origins.includes(origin) || origin === draft.origin)
      return;
    setWelcomeEntry(false);
    update({ origin });
    setHomeRevision((value) => value + 1);
  };

  const finishOnboarding = async () => {
    if (onboardingLock.current) return;
    onboardingLock.current = true;
    setOnboardingBusy(true);
    setOnboardingError("");
    try {
      if (!profile?.onboarding_completed) {
        setProfile(
          await api<UserProfile>("/profile/onboarding", initData.current, {
            method: "PUT",
          }),
        );
      }
      navigate(pendingShare.current && trip ? "result" : "home");
      setWelcomeEntry(!pendingShare.current);
      pendingShare.current = null;
      setOnboarded(true);
    } catch (err) {
      setOnboardingError((err as Error).message);
    } finally {
      onboardingLock.current = false;
      setOnboardingBusy(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    setBooting(true);
    setError("");
    initData.current = rawLaunch();
    try {
      window.WebApp?.ready?.();
    } catch {
      /* Optional bridge method. */
    }
    const boot = async () => {
      try {
        const [user, settings, userProfile] = await Promise.all([
          api<Identity>("/auth/me", initData.current, {
            signal: controller.signal,
          }),
          api<AppConfig>("/app-config", initData.current, {
            signal: controller.signal,
          }).then((settings) => {
            if (!controller.signal.aborted) setConfig(settings);
            return settings;
          }),
          api<UserProfile>("/profile", initData.current, {
            signal: controller.signal,
          }),
        ]);
        if (controller.signal.aborted) return;
        prefix.current = `nearby:v2:${user.mode}:${user.user.id}:`;
        setIdentity(user);
        setProfile(userProfile);
        setOnboarded(userProfile.onboarding_completed);
        setConfig(settings);
        setDraft(
          restoreDraft(
            readStorage<Partial<Draft> | null>(prefix.current + "draft", null),
            settings,
            userProfile.preferences && {
              origin: userProfile.preferences.origin,
              pace: userProfile.preferences.pace,
              interests: userProfile.preferences.interests,
              max_distance_km: userProfile.preferences.max_distance_km,
              preferred_transport: userProfile.preferences.preferred_transport,
              has_car: userProfile.preferences.preferred_transport === "car",
            },
          ),
        );
        const savedStep = readStorage<number>(prefix.current + "step", 0);
        setStep(
          Number.isInteger(savedStep) && savedStep >= 0 && savedStep <= 4
            ? savedStep
            : 0,
        );
        const savedJob = readStorage<string | null>(
          prefix.current + "job",
          null,
        );
        const savedTrip = readStorage<string | null>(
          prefix.current + "trip",
          null,
        );
        const sharedToken = sharedLaunch() || pendingShare.current;
        if (sharedToken) {
          pendingShare.current = sharedToken;
          try {
            const plan = await api<TripPlan>(`/shared-trips/${sharedToken}/import`, initData.current, {
              method: "POST", signal: controller.signal,
            });
            if (controller.signal.aborted) return;
            setTrip({ plan });
            writeStorage(prefix.current + "trip", plan.id);
            navigate("result");
            if (userProfile.onboarding_completed) pendingShare.current = null;
          } catch (err) {
            if (!controller.signal.aborted) setError((err as Error).message);
          }
        } else if (savedJob && typeof savedJob === "string") {
          setJobId(savedJob);
          navigate("loading");
        } else if (savedTrip && typeof savedTrip === "string") {
          try {
            const plan = await api<TripPlan>(
              `/trips/${encodeURIComponent(savedTrip)}`,
              initData.current,
              { signal: controller.signal },
            );
            if (!controller.signal.aborted) setTrip({ plan });
          } catch (err) {
            if (!controller.signal.aborted) {
              if (err instanceof ApiError && err.status === 404) {
                writeStorage(prefix.current + "trip", null);
              }
              setError(
                "Не удалось открыть прошлую поездку. Попробуйте ещё раз в разделе «Мои поездки».",
              );
            }
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) setError((err as Error).message);
      } finally {
        if (!controller.signal.aborted) setBooting(false);
      }
    };
    void boot();
    return () => controller.abort();
  }, [bootRetry, navigate]);
  useEffect(() => {
    if (prefix.current && draft) writeStorage(prefix.current + "draft", draft);
  }, [draft]);
  useEffect(() => {
    if (prefix.current) writeStorage(prefix.current + "step", step);
  }, [step]);

  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    setPollError("");
    const poll = async () => {
      try {
        const status = await api<Job>(
          `/trips/jobs/${encodeURIComponent(jobId)}`,
          initData.current,
          { signal: controller.signal },
        );
        if (controller.signal.aborted) return;
        setJob(status);
        if (status.status === "succeeded" && status.result) {
          setTrip({ plan: status.result });
          setJobId(null);
          writeStorage(prefix.current + "job", null);
          writeStorage(prefix.current + "trip", status.result.id);
          navigate("result");
        } else if (status.status === "failed") {
          setJobId(null);
          writeStorage(prefix.current + "job", null);
          setSubmitError(
            status.error?.error ||
              "Не получилось собрать поездку. Попробуйте ещё раз.",
          );
          setStep(4);
          navigate("wizard");
        } else timer = setTimeout(poll, 1500);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 404) {
          setJobId(null);
          writeStorage(prefix.current + "job", null);
          setError(
            "Задача больше недоступна: сервер мог перезапуститься. Анкета сохранена.",
          );
          navigate("home");
        } else setPollError((err as Error).message);
      }
    };
    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [jobId, retry, navigate]);

  const back = useCallback(() => {
    if (screen === "wizard" && step > 0) setStep(step - 1);
    else if (screen === "profile") navigate(profileReturn.current);
    else navigate("home");
  }, [navigate, screen, step]);
  useEffect(() => {
    const bridge = window.WebApp;
    if (!initData.current || !bridge) return;
    try {
      if (onboarded && screen !== "home") bridge.BackButton?.show?.();
      else bridge.BackButton?.hide?.();
      bridge.BackButton?.onClick?.(back);
      if (screen === "wizard" || jobId) bridge.enableClosingConfirmation?.();
      else bridge.disableClosingConfirmation?.();
    } catch {
      /* Native UI support varies; app controls always remain. */
    }
    return () => {
      try {
        bridge.BackButton?.offClick?.(back);
      } catch {
        /* Optional method. */
      }
    };
  }, [screen, jobId, back, onboarded]);

  const start = (patch?: Partial<Draft>) => {
    setSubmitError("");
    if (jobId) {
      navigate("loading");
      return;
    }
    if (patch) update(patch);
    navigate("wizard");
  };
  const submit = async () => {
    if (!draft || submitLock.current) return;
    if (jobId) {
      navigate("loading");
      return;
    }
    submitLock.current = true;
    setBusy(true);
    setSubmitError("");
    try {
      const result = await api<{ id: string }>(
        "/trips/jobs",
        initData.current,
        { method: "POST", body: JSON.stringify(toRequest(draft)) },
      );
      setJob(null);
      setJobId(result.id);
      writeStorage(prefix.current + "job", result.id);
      navigate("loading");
    } catch (err) {
      setSubmitError((err as Error).message);
    } finally {
      setBusy(false);
      submitLock.current = false;
    }
  };

  if (!booting && !identity) {
    const botUrl = (config?.bot_url || "https://max.ru/t539_hakaton_max_bot?startapp")
      + (pendingShare.current ? `=trip_${pendingShare.current}` : "");
    return (
      <MaxEntry
        botUrl={botUrl}
        sharedTrip={Boolean(pendingShare.current)}
        error={initData.current ? error : undefined}
      />
    );
  }
  const navVisible = ["home", "trips", "about"].includes(screen);
  return (
    <>
      {!booting && !onboarded ? (
        <motion.div
          key="onboarding"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            duration: reducedMotion ? 0 : 0.24,
            ease: "easeInOut",
          }}
        >
          <Onboarding
            onDone={finishOnboarding}
            busy={onboardingBusy}
            error={onboardingError}
          />
        </motion.div>
      ) : (
        <motion.div
          key={screen === "home" ? `home-${homeRevision}` : screen}
          data-ui={`app-shell screen-${screen}`}
          className="min-h-[100dvh] [&[data-ui~=screen-loading]]:flex [&[data-ui~=screen-loading]]:flex-col"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            duration: reducedMotion ? 0 : 0.12,
            ease: "easeInOut",
          }}
        >
          <header data-ui="app-header" className={appHeaderStyles}>
            <button
              data-ui="brand-button"
              className="[background:none] p-0 flex items-center"
              aria-label="Рядом — на главную"
              onClick={() => navigate("home")}
            >
              <Brand />
            </button>
            <div
              data-ui="header-right"
              className="flex items-center gap-6.5"
            >
              <span
                data-ui="header-tag"
                className="text-[11px] font-[750] tracking-[1.6px] text-[#9b9fb0] mobile:hidden
                  mobile-type:text-[10px]"
              >
                МИНИ-ПУТЕШЕСТВИЯ В MAX
              </span>
              <button
                data-ui="avatar"
                className={avatarStyles}
                aria-label="Открыть профиль"
                onClick={openProfile}
              >
                <ProfileAvatar user={identity?.user} />
              </button>
            </div>
          </header>
          <main
            data-ui={`app-main ${navVisible ? "with-nav" : ""}`}
            className={
              appMainStyles +
              " " +
              (navVisible
                ? "[[data-ui~=app-main]&]:pb-26 mobile:[[data-ui~=app-main]&]:pb-[calc(78px_+_var(--app-safe-bottom))]"
                : "")
            }
          >
            {error && (
              <Notice error onClose={() => setError("")}>
                {error}
              </Notice>
            )}
            {booting ? (
              <div
                data-ui="boot-skeleton"
                className="max-w-175 my-5 mx-auto [&_>_div]:rounded-[22px]
                  [&_>_div]:[background:linear-gradient(110deg,_#edeff5_8%,_#f7f8fc_18%,_#edeff5_33%)]
                  [&_>_div]:[background-size:200%_100%]
                  [&_>_div]:[animation:shimmer_1.5s_linear_infinite] [&_>_div:first-child]:w-[60%]
                  [&_>_div:first-child]:h-17.5 [&_>_div:first-child]:mb-5 [&_>_div:nth-child(2)]:h-75
                  [&_>_div:nth-child(3)]:h-27.5 [&_>_div:nth-child(3)]:mt-4.5"
                aria-label="Загружаем приложение"
                role="status"
              >
                <div />
                <div />
                <div />
              </div>
            ) : !identity || !draft || !config ? (
              <div data-ui="empty-state" className={emptyStateStyles}>
                <span data-ui="soft-icon blue" className={softBlueIconStyles}>
                  <Navigation size={30} />
                </span>
                <h1>Не удалось подключиться</h1>
                <p>
                  Откройте «Рядом» через бота MAX — так мы сможем подключить ваш
                  профиль.
                </p>
                <Primary onClick={() => setBootRetry((value) => value + 1)}>
                  Попробовать ещё раз
                </Primary>
              </div>
            ) : (
              <>
                {screen === "home" && (
                  <motion.div
                    data-ui="home-page"
                    initial={welcomeEntry && !reducedMotion ? { y: 14 } : false}
                    animate={{ y: 0 }}
                    transition={{
                      duration: reducedMotion ? 0 : 0.42,
                      ease: "easeOut",
                    }}
                  >
                    <div
                      data-ui="home-heading"
                      className="flex justify-between items-center mt-0 mx-0 mb-6 mobile:[align-items:end] mobile:mt-0
                        mobile:mx-0 mobile:mb-6 mobile:gap-2.5 narrow-type:flex-wrap
                        phone-stack:flex-col phone-stack:items-start phone-stack:gap-3 short:mb-5
                        [&_h1]:text-[43px] [&_h1]:font-extrabold [&_h1]:tracking-[-2px]
                        [&_h1]:leading-[1.16] [&_h1]:mt-3 tablet:[&_h1]:text-[37px]
                        mobile:[&_h1]:text-[35px] mobile:[&_h1]:font-extrabold
                        mobile:[&_h1]:tracking-[-1.65px] mobile:[&_h1]:leading-[1.18]
                        mobile:[&_h1]:mt-[11px] narrow:[&_h1]:text-[31px]
                        phone-heading:[&_h1]:text-[clamp(30px,_8.7vw,_35px)]
                        short-mobile:[&_h1]:text-[30px] short-mobile:[&_h1]:mt-2"
                    >
                      <div>
                        <span data-ui="eyebrow" className={eyebrowStyles}>
                          ВАШ СЛЕДУЮЩИЙ ХОРОШИЙ ДЕНЬ
                        </span>
                        <h1>
                          Сменим
                          <br
                            data-ui="mobile-break"
                            className="hidden mobile:block"
                          />{" "}
                          обстановку
                          <span data-ui="blue-text" className="text-brand">
                            ?
                          </span>
                        </h1>
                      </div>
                      <label
                        data-ui="origin-pill"
                        className="relative flex items-center gap-[7px] [border:1px_solid_#e5e8f0] bg-white
                          rounded-[30px] py-0 px-[13px] text-[#5f6577] w-[fit-content] max-w-full
                          min-h-10 shrink-0 mobile:py-0 mobile:px-3 mobile:m-0 mobile:min-h-9
                          mobile:gap-[7px] [&_>_span]:text-[12px] [&_>_span]:font-[650]
                          [&_>_span]:whitespace-nowrap [&:focus-within]:[outline:2px_solid_#a3b1ff]
                          [&:focus-within]:outline-offset-2 [&_select]:absolute [&_select]:top-0
                          [&_select]:right-0 [&_select]:bottom-0 [&_select]:left-0
                          [&_select]:size-full [&_select]:min-h-0 [&_select]:opacity-0
                          [&_select]:cursor-pointer [&_select]:text-[16px] mobile:[&_svg]:w-[13px]"
                      >
                        <MapPin size={15} aria-hidden="true" />
                        <span aria-hidden="true">{draft.origin}</span>
                        <ChevronDown size={14} aria-hidden="true" />
                        <select
                          aria-label="Город отправления"
                          value={draft.origin}
                          onChange={(event) => changeOrigin(event.target.value)}
                        >
                          {config.origins.map((origin) => (
                            <option key={origin}>{origin}</option>
                          ))}
                        </select>
                      </label>
                    </div>
                    <div
                      data-ui="home-grid"
                      className="grid grid-cols-[1.38fr_1fr] gap-[25px] desktop-fit:gap-5
                        tablet:grid-cols-[1.2fr_1fr] mobile:flex mobile:flex-col mobile:gap-6"
                    >
                      <section
                        data-ui="adventure-card"
                        className="flex flex-col rounded-[28px] relative overflow-hidden bg-[#dae6df] min-h-[427px]
                          text-white mobile:min-h-[355px] mobile:rounded-3xl short:min-h-0
                          [&_>_img]:size-full [&_>_img]:object-cover [&_>_img]:absolute
                          [&_>_img]:top-0 [&_>_img]:right-0 [&_>_img]:bottom-0 [&_>_img]:left-0
                          [&_>_img]:object-[50%_center]"
                      >
                        <img
                          src={
                            draft.origin === "Санкт-Петербург"
                              ? journeySpb
                              : journey
                          }
                          alt={
                            draft.origin === "Санкт-Петербург"
                              ? "Северный пейзаж: сосны, озеро и старинный город"
                              : "Город и загородный пейзаж у реки"
                          }
                        />
                        <div
                          data-ui="adventure-gradient"
                          className="absolute top-0 right-0 bottom-0 left-0
                            [background:linear-gradient(_180deg,_#13373920_0%,_#142f320a_25%,_#172d3b65_51%,_#152836e8_100%_)]"
                        />
                        <div
                          data-ui="adventure-top"
                          className="absolute top-5.5 left-6 right-6 flex items-center justify-between
                            mobile:top-[17px] mobile:left-4.5 mobile:right-4.5 narrow:left-[15px]
                            narrow:right-[15px] [&_>_span]:flex [&_>_span]:gap-[7px]
                            [&_>_span]:items-center [&_>_span]:text-[11px] [&_>_span]:font-bold
                            [&_>_span]:tracking-[0.65px] [&_>_span]:bg-[#263b3e42]
                            [&_>_span]:[backdrop-filter:blur(14px)] [&_>_span]:py-[9px]
                            [&_>_span]:px-[11px] [&_>_span]:rounded-[30px]
                            [&_>_span]:[border:1px_solid_#ffffff30] mobile:[&_>_span]:text-[11px]
                            mobile:[&_>_span]:py-2 mobile:[&_>_span]:px-2.5 mobile:[&_>_span]:gap-1.5
                            mobile:[&_>_span]:tracking-[0.5px] narrow:[&_>_span]:text-[11px]
                            mobile-type:[&_>_span]:text-[9px] mobile-type:[&_>_span]:tracking-[0.3px]
                            narrow-type:[&_>_span]:text-[8px] mobile:[&_>_span_>_svg]:size-3"
                        >
                          <span>
                            <Sparkles size={14} /> ВАШ ЛИЧНЫЙ ПЛАН НА ВЫХОДНЫЕ
                          </span>
                          <div
                            data-ui="round-stamp"
                            className="size-[45px] [border:1px_solid_#ffffff60] bg-[#ffffff18]
                              [backdrop-filter:blur(10px)] rounded-[50%] grid place-items-center
                              [transform:rotate(10deg)] mobile:size-[35px] mobile:[&_>_svg]:size-5"
                          >
                            <Navigation size={24} />
                          </div>
                        </div>
                        <div
                          data-ui="adventure-copy"
                          className="relative flex flex-1 flex-col pt-[175px] px-7.5 tablet:px-[23px] mobile:pt-36.5
                            mobile:px-[21px] narrow:px-4.5 short:pt-25
                            short-narrow:pt-21 [&_h2]:text-[37px] [&_h2]:tracking-[-1.6px]
                            [&_h2]:leading-[1.16] [&_h2]:font-extrabold tablet:[&_h2]:text-[32px]
                            mobile:[&_h2]:text-[30px] mobile:[&_h2]:tracking-[-1.15px]
                            mobile:[&_h2]:leading-[1.16] narrow:[&_h2]:text-[29px]
                            short-mobile:[&_h2]:text-[28px] [&_p]:text-[12px] [&_p]:leading-[1.8]
                            [&_p]:text-[#eff5f2db] [&_p]:mt-[13px] [&_p]:mx-0 [&_p]:mb-5.5
                            mobile:[&_p]:text-[11px] mobile:[&_p]:leading-[1.8] mobile:[&_p]:mt-[11px]
                            mobile:[&_p]:mx-0 mobile:[&_p]:mb-4.5 mobile:[&_p]:max-w-[285px]
                            mobile-type:[&_p]:text-[13px] short-mobile:[&_p]:mt-2.5
                            short-mobile:[&_p]:mx-0 short-mobile:[&_p]:mb-4"
                        >
                          <h2>
                            Далеко ехать
                            <br />
                            необязательно.
                          </h2>
                          <p>
                            Новые места, местная кухня и целый день
                            <br
                              data-ui="desktop-break"
                              className="mobile:hidden"
                            />{" "}
                            для себя. Соберём всё в одну поездку.
                          </p>
                          <Primary onClick={() => start()}>
                            {jobId
                              ? "Вернуться к генерации"
                              : "Спланировать поездку"}
                          </Primary>
                          <span
                            data-ui="adventure-caption"
                            className="text-[11px] flex flex-1 items-center justify-center text-center text-[#e0e9e7b8] py-[16.5px] mobile:text-[11px]
                              mobile:py-[14.5px] short-mobile:py-[13px]"
                          >
                            5 простых шагов · ваш темп и бюджет
                          </span>
                        </div>
                      </section>
                      <div data-ui="home-side">
                        <section data-ui="mood-section">
                          <div
                            data-ui="section-heading"
                            className={sectionHeadingStyles}
                          >
                            <h2>Как хочется отдохнуть?</h2>
                            <span>Начнём с настроения</span>
                          </div>
                          <div
                            data-ui="mood-grid"
                            className="grid grid-cols-[1fr_1fr] gap-3"
                          >
                            <button
                              data-ui="mood-card green"
                              className="flex flex-col relative overflow-hidden rounded-[21px] py-[19px] px-4
                                text-left min-h-50.5 [transition:transform_0.2s] tablet:py-[17px]
                                tablet:px-[11px] mobile:min-h-[183px] mobile:py-[17px]
                                mobile:px-[15px] mobile:rounded-[18px] narrow:py-[15px] narrow:px-3
                                mobile-type:min-h-48.5 [&:hover]:[transform:translateY(-3px)]
                                [&_>_span:nth-child(2)]:relative [&_>_span:nth-child(2)]:mt-auto
                                [&_strong]:block [&_strong]:text-[12px] [&_strong]:font-extrabold
                                [&_strong]:leading-[1.4] tablet:[&_strong]:text-[11px]
                                mobile:[&_strong]:text-[11px] narrow:[&_strong]:text-[11px]
                                mobile-type:[&_strong]:text-[13px]
                                mobile-type:[&_strong]:leading-[1.4]
                                narrow-type:[&_strong]:text-[12px] [&_small]:block
                                [&_small]:text-[11px] [&_small]:mt-1.5 [&_small]:text-[#778574]
                                tablet:[&_small]:text-[11px] mobile:[&_small]:text-[11px]
                                mobile:[&_small]:mt-[5px] mobile-type:[&_small]:text-[11px]
                                mobile-type:[&_small]:leading-[1.6] [&_>_svg]:absolute
                                [&_>_svg]:right-3.5 [&_>_svg]:top-3.5 [&_>_svg]:text-[#83967b]
                                mobile:[&_>_svg]:size-4 mobile:[&_>_svg]:right-[13px]
                                mobile:[&_>_svg]:top-3.5 mobile-type:[&_>_svg]:top-[15px]
                                mobile-type:[&_>_svg]:right-3 [[data-ui~=mood-card]&]:bg-[#eaf0e5]"
                              onClick={() => {
                                setStep(0);
                                start({
                                  interests: ["Природа", "Прогулки"],
                                  pace: "relaxed",
                                });
                              }}
                            >
                              <span
                                data-ui="mood-drawing nature-drawing"
                                className="h-25 w-full block relative mobile:h-22 [&_span]:absolute
                                  [&_span]:bg-[#89a889] [&_span]:rounded-[60%_60%_30%_30%]
                                  [&_span]:h-[65px] [&_span]:w-8.5 [&_span]:left-6 [&_span]:top-1.5
                                  [&_span]:[transform:rotate(-7deg)]
                                  [&_span]:[box-shadow:inset_-8px_-3px_0_#557d7220]
                                  [&_span::after]:[content:''] [&_span::after]:absolute
                                  [&_span::after]:w-[3px] [&_span::after]:h-[39px]
                                  [&_span::after]:bg-[#697e60] [&_span::after]:-bottom-3
                                  [&_span::after]:left-4 [&_span::after]:rounded-[3px]
                                  [&_span:nth-child(2)]:left-[59px] [&_span:nth-child(2)]:top-4.5
                                  [&_span:nth-child(2)]:h-[47px] [&_span:nth-child(2)]:w-7.5
                                  [&_span:nth-child(2)]:bg-[#adc096]
                                  [&_span:nth-child(2)]:[transform:rotate(10deg)]
                                  [&_span:nth-child(3)]:left-[9px] [&_span:nth-child(3)]:top-[47px]
                                  [&_span:nth-child(3)]:h-4.5 [&_span:nth-child(3)]:w-19.5
                                  [&_span:nth-child(3)]:bg-[#d8e3ce]
                                  [&_span:nth-child(3)]:rounded-[50%]
                                  [&_span:nth-child(3)]:[transform:rotate(0)]
                                  [&_span:nth-child(3)]:z-0 [&_span:nth-child(3)::after]:hidden"
                              >
                                <span />
                                <span />
                                <span />
                              </span>
                              <span>
                                <strong>Поближе к природе</strong>
                                <small>Выдохнуть и замедлиться</small>
                              </span>
                              <ArrowUpRight size={18} />
                            </button>
                            <button
                              data-ui="mood-card peach"
                              className="flex flex-col relative overflow-hidden rounded-[21px] py-[19px] px-4
                                text-left min-h-50.5 [transition:transform_0.2s] tablet:py-[17px]
                                tablet:px-[11px] mobile:min-h-[183px] mobile:py-[17px]
                                mobile:px-[15px] mobile:rounded-[18px] narrow:py-[15px] narrow:px-3
                                mobile-type:min-h-48.5 [&:hover]:[transform:translateY(-3px)]
                                [&_>_span:nth-child(2)]:relative [&_>_span:nth-child(2)]:mt-auto
                                [&_strong]:block [&_strong]:text-[12px] [&_strong]:font-extrabold
                                [&_strong]:leading-[1.4] tablet:[&_strong]:text-[11px]
                                mobile:[&_strong]:text-[11px] narrow:[&_strong]:text-[11px]
                                mobile-type:[&_strong]:text-[13px]
                                mobile-type:[&_strong]:leading-[1.4]
                                narrow-type:[&_strong]:text-[12px] [&_small]:block
                                [&_small]:text-[11px] [&_small]:mt-1.5 [&_small]:text-[#778574]
                                tablet:[&_small]:text-[11px] mobile:[&_small]:text-[11px]
                                mobile:[&_small]:mt-[5px] mobile-type:[&_small]:text-[11px]
                                mobile-type:[&_small]:leading-[1.6] [&_>_svg]:absolute
                                [&_>_svg]:right-3.5 [&_>_svg]:top-3.5 [&_>_svg]:text-[#83967b]
                                mobile:[&_>_svg]:size-4 mobile:[&_>_svg]:right-[13px]
                                mobile:[&_>_svg]:top-3.5 mobile-type:[&_>_svg]:top-[15px]
                                mobile-type:[&_>_svg]:right-3 [[data-ui~=mood-card]&]:bg-[#faede3]
                                [[data-ui~=mood-card]&_small]:text-[#ae8572]
                                [[data-ui~=mood-card]&_>_svg]:text-[#c49a7d]"
                              onClick={() => {
                                setStep(0);
                                start({
                                  interests: ["История", "Местная кухня"],
                                  pace: "balanced",
                                });
                              }}
                            >
                              <span
                                data-ui="mood-drawing city-drawing"
                                className="h-25 w-full block relative mobile:h-22 [&_span]:h-12.5
                                  [&_span]:w-[33px] [&_span]:bg-[#cf9982] [&_span]:absolute
                                  [&_span]:left-[21px] [&_span]:top-[27px] [&_span]:rounded-[3px]
                                  [&_span]:[box-shadow:inset_-7px_0_0_#aa6c6015]
                                  [&_span::before]:[content:''] [&_span::before]:absolute
                                  [&_span::before]:[border-left:22px_solid_transparent]
                                  [&_span::before]:[border-right:22px_solid_transparent]
                                  [&_span::before]:[border-bottom:23px_solid_#b46e5a]
                                  [&_span::before]:left-[-5px] [&_span::before]:-top-5
                                  [&_span::after]:[content:''] [&_span::after]:absolute
                                  [&_span::after]:bg-[#fff4d9] [&_span::after]:left-2.5
                                  [&_span::after]:top-[13px] [&_span::after]:w-[7px]
                                  [&_span::after]:h-[11px] [&_span::after]:rounded-[5px_5px_0_0]
                                  [&_span::after]:[box-shadow:12px_0_0_#fff4d9,_0_19px_0_#fff4d9]
                                  [&_span:nth-child(2)]:left-15 [&_span:nth-child(2)]:top-[15px]
                                  [&_span:nth-child(2)]:h-[61px] [&_span:nth-child(2)]:w-6
                                  [&_span:nth-child(2)]:bg-[#e3bb93]
                                  [&_span:nth-child(2)::before]:[border-left-width:16px]
                                  [&_span:nth-child(2)::before]:[border-right-width:16px]
                                  [&_span:nth-child(2)::before]:[border-bottom-color:#75949e]
                                  [&_span:nth-child(2)::before]:-left-1
                                  [&_span:nth-child(2)::after]:left-2
                                  [&_span:nth-child(2)::after]:[box-shadow:0_19px_0_#fff4d9]
                                  [&_span:nth-child(3)]:h-[5px] [&_span:nth-child(3)]:w-[85px]
                                  [&_span:nth-child(3)]:bg-[#e7cabb] [&_span:nth-child(3)]:left-2.5
                                  [&_span:nth-child(3)]:top-19.5 [&_span:nth-child(3)]:rounded-[50%]
                                  [&_span:nth-child(3)::before]:hidden
                                  [&_span:nth-child(3)::after]:hidden"
                              >
                                <span />
                                <span />
                                <span />
                              </span>
                              <span>
                                <strong>Город с историей</strong>
                                <small>Улочки, музеи и кофе</small>
                              </span>
                              <ArrowUpRight size={18} />
                            </button>
                            {([
                              { title: "За местным вкусом", subtitle: "Уютные кафе и новые вкусы", Icon: Coffee,
                                interests: ["Местная кухня", "Прогулки"], pace: "relaxed", color: "#eee9f7", ink: "#9482b0" },
                              { title: "Больше движения", subtitle: "Тропы и маленькие открытия", Icon: Route,
                                interests: ["Активный отдых", "Природа"], pace: "intensive", color: "#e5eef6", ink: "#7b9bb6" },
                            ] as const).map((mood) => <button key={mood.title} data-ui="mood-card"
                              className="flex flex-col relative overflow-hidden rounded-[21px] py-[19px] px-4 text-left min-h-50.5
                                mobile:min-h-[183px] mobile:py-[17px] mobile:px-[15px] mobile:rounded-[18px]
                                narrow:px-3 mobile-type:min-h-48.5 transition-transform hover:-translate-y-[3px]"
                              style={{ background: mood.color }} onClick={() => { setStep(0); start({ interests: [...mood.interests], pace: mood.pace }); }}>
                              <span className="h-25 mobile:h-22 flex items-center pl-3" aria-hidden="true">
                                <mood.Icon size={65} strokeWidth={1.25} style={{ color: mood.ink }} />
                              </span>
                              <span className="mt-auto"><strong className="block text-[12px] font-extrabold leading-[1.4] mobile-type:text-[13px] narrow-type:text-[12px]">{mood.title}</strong>
                                <small className="block text-[11px] mt-1.5 leading-[1.6]" style={{ color: mood.ink }}>{mood.subtitle}</small></span>
                              <ArrowUpRight size={18} className="absolute right-3.5 top-3.5" style={{ color: mood.ink }} />
                            </button>)}
                          </div>
                        </section>
                        <section
                          data-ui="how-card"
                          className="flex gap-[15px] mt-5 [border:1px_solid_var(--line)] bg-white
                            rounded-[20px] py-5.5 px-[19px] tablet:py-4.5 tablet:px-3.5 tablet:gap-2.5
                            mobile:p-4.5 mobile:rounded-[18px] mobile:mt-[15px] mobile:gap-[13px]
                            mobile-spacing:mt-4 [&_h3]:text-[15px] [&_h3]:leading-[1.65]
                            [&_h3]:font-[750] tablet:[&_h3]:text-[13px] mobile:[&_h3]:text-[13px]
                            mobile:[&_h3]:leading-[1.7] [&_p]:text-[11px] [&_p]:leading-[1.8]
                            [&_p]:text-muted [&_p]:mt-2 tablet:[&_p]:text-[11px]
                            mobile:[&_p]:text-[11px] mobile:[&_p]:leading-[1.8] mobile:[&_p]:mt-1.5
                            mobile-type:[&_p]:text-[13px]"
                        >
                          <span
                            data-ui="soft-icon blue"
                            className={softBlueIconStyles}
                          >
                            <Route size={22} />
                          </span>
                          <div>
                            <h3>
                              Вы выбираете настроение.
                              <br />
                              Мы продумываем детали.
                            </h3>
                            <p>
                              Программа, прогноз, дорога и примерный бюджет —
                              без десятка открытых вкладок.
                            </p>
                          </div>
                        </section>
                      </div>
                    </div>
                    <PresetCards
                      origin={draft.origin}
                      onOpen={(selected) => {
                        setPreset(selected);
                        navigate("preset");
                      }}
                    />
                    <footer
                      data-ui="home-footer"
                      className="flex flex-col items-center gap-2 pt-4 mt-4 [border-top:1px_solid_var(--line)]
                        text-muted text-center text-[12px] leading-[1.6] mobile:mt-4
                        [&_>_svg]:text-[#8d9cce] [&_p]:m-0 [&_p_>_span]:whitespace-nowrap
                        [&_p_>_span]:text-[#64739a]"
                    >
                      <Heart size={16} aria-hidden="true" />
                      <p>
                        Хорошие выходные начинаются
                        <br />с маленького <span>«поехали».</span>
                      </p>
                    </footer>
                  </motion.div>
                )}
                {screen === "wizard" && (
                  <Wizard
                    initData={initData.current}
                    draft={draft}
                    update={update}
                    config={config}
                    step={step}
                    setStep={setStep}
                    onExit={() => navigate("home")}
                    onSubmit={submit}
                    busy={busy}
                    serverError={submitError}
                  />
                )}
                {screen === "preset" && preset && (
                  <PresetDetail
                    key={preset.id}
                    preset={preset}
                    hasActiveJob={Boolean(jobId)}
                    onBack={() => navigate("home")}
                    onUse={() => {
                      if (jobId) {
                        navigate("loading");
                        return;
                      }
                      setStep(0);
                      const lastStart = addDays(
                        config.last_trip_date,
                        1 - preset.days.length,
                      );
                      start({
                        origin: preset.origin,
                        destination: preset.city,
                        destinationMode: "manual",
                        days: preset.days.length,
                        start_date:
                          draft.start_date > lastStart
                            ? lastStart
                            : draft.start_date,
                        interests: [...preset.interests],
                        pace: preset.pace,
                        max_travel_minutes: preset.maxTravelMinutes,
                        budget_rub: Math.max(
                          draft.budget_rub,
                          preset.budgetRub,
                        ),
                      });
                    }}
                  />
                )}
                {screen === "loading" && (
                  <Loading
                    job={job}
                    error={pollError}
                    retry={() => setRetry((value) => value + 1)}
                    onBack={() => navigate("home")}
                  />
                )}
                {screen === "result" && trip && (
                  <TripResult
                    {...trip}
                    key={trip.plan.id}
                    initData={initData.current}
                    onPlanChange={(plan) => setTrip((current) =>
                      current?.plan.id === plan.id ? { plan } : current
                    )}
                    onBack={() => navigate("home")}
                    onEdit={() => {
                      setStep(0);
                      start();
                    }}
                  />
                )}
                {screen === "trips" && (
                  <div data-ui="trips-page" className={tripsPageStyles}>
                    <span data-ui="eyebrow" className={eyebrowStyles}>
                      ЕЩЁ ОДИН ПОВОД ВЫБРАТЬСЯ
                    </span>
                    <h1 className="mb-3">Мои поездки</h1>
                    {jobId && (
                      <button
                        data-ui="active-job"
                        className="w-full flex gap-[17px] items-center text-left p-6
                          [border:1px_solid_var(--line)] rounded-[22px] mb-4.5 text-brand bg-[#eff3ff]
                          border-[#dfe6fc] mobile:p-4.5 [&_>_span]:flex-1 [&_strong]:block
                          [&_strong]:text-[12px] mobile:[&_strong]:text-[11px] [&_small]:block
                          [&_small]:text-[11px] [&_small]:text-[#95a2bb] [&_small]:mt-1.5
                          mobile:[&_small]:text-[11px]"
                        onClick={() => navigate("loading")}
                      >
                        <Sparkles
                          data-ui="pulse"
                          className="[animation:bob_3s_ease-in-out_infinite]"
                          size={22}
                        />
                        <span>
                          <strong>Готовим ваш маршрут</strong>
                          <small>{job?.message || "Задача запущена"}</small>
                        </span>
                        <ChevronRight size={20} />
                      </button>
                    )}
                    <MyTrips
                      initData={initData.current}
                      onCreate={() => start()}
                      onOpen={(plan) => {
                        setTrip({ plan });
                        writeStorage(prefix.current + "trip", plan.id);
                        navigate("result");
                      }}
                    />
                  </div>
                )}
                {screen === "profile" && profile && (
                  <Profile user={identity.user} profile={profile} config={config}
                    initData={initData.current} onBack={back} onSave={(next) => {
                      setProfile(next);
                      if (next.preferences) update({ origin: next.preferences.origin,
                        pace: next.preferences.pace, interests: next.preferences.interests,
                        max_distance_km: next.preferences.max_distance_km,
                        preferred_transport: next.preferences.preferred_transport,
                        has_car: next.preferences.preferred_transport === "car" });
                    }} />
                )}
                {screen === "about" && (
                  <div data-ui="about-page" className={tripsPageStyles}>
                    <span data-ui="eyebrow" className={eyebrowStyles}>
                      ПРИЯТНО ПОЗНАКОМИТЬСЯ
                    </span>
                    <h1 className="mb-3">
                      {identity.mode === "max"
                        ? `${identity.user.first_name}, поехали?`
                        : "Большие открытия рядом."}
                    </h1>
                    <p
                      data-ui="page-description"
                      className="leading-[1.7] text-[15px] mobile:text-[12px] mobile:leading-[1.7]
                        mobile-type:text-[14px] text-[#687389]"
                    >
                      Помогаем придумать поездку выходного дня — с вниманием к
                      вашему времени, интересам и бюджету.
                    </p>
                    <button
                      data-ui="about-profile"
                      onClick={openProfile}
                      aria-label="Открыть профиль из раздела о сервисе"
                      className="w-full text-left flex gap-[13px] items-center p-4 rounded-[20px] bg-white
                        [border:1px_solid_var(--line)] my-4 mx-0 mobile:p-3.5 mobile:my-3.5
                        mobile:mx-0 [&_>_div]:flex-1 [&_>_div]:min-w-0 [&_>_div]:wrap-anywhere
                        [&_strong]:text-[12px] [&_strong]:block [&_#session-label]:text-[12px]
                        [&_#session-label]:leading-[1.55] [&_#session-label]:text-muted
                        [&_#session-label]:block [&_#session-label]:mt-[5px] [&_>_svg]:text-[#88a189]"
                    >
                      <span data-ui="avatar" className={avatarStyles}>
                        <ProfileAvatar user={identity.user} />
                      </span>
                      <div>
                        <strong>
                          {[identity.user.first_name, identity.user.last_name]
                            .filter(Boolean)
                            .join(" ")}
                        </strong>
                        {identity.user.username && (
                          <span>@{identity.user.username}</span>
                        )}
                        <span id="session-label">
                          {identity.mode === "max"
                            ? "Все ваши поездки привязаны к профилю в MAX"
                            : "Локальный режим"}
                        </span>
                      </div>
                      <ChevronRight size={19} />
                    </button>
                    <section
                      data-ui="about-info"
                      className="bg-white [border:1px_solid_var(--line)] rounded-[23px] p-[25px]
                        mobile:p-[21px] mobile:rounded-[20px] [&_>_h2]:text-[18px]
                        [&_>_h2]:tracking-[-0.5px] [&_>_h2]:font-[750] [&_>_h2]:mb-[25px]
                        mobile:[&_>_h2]:text-[16px] mobile:[&_>_h2]:leading-[1.5]
                        mobile:[&_>_h2]:tracking-[-0.4px] mobile:[&_>_h2]:mb-5 [&_>_div]:flex
                        [&_>_div]:gap-[15px] [&_>_div]:mt-5.5 mobile:[&_>_div]:gap-3
                        mobile:[&_>_div]:mt-5.5 [&_h3]:text-[12px] [&_h3]:font-[750]
                        [&_h3]:leading-[1.7] mobile:[&_h3]:text-[11px] mobile-type:[&_h3]:text-[13px]
                        [&_p]:text-[11px] [&_p]:leading-[1.9] [&_p]:text-[#99a2b3] [&_p]:mt-1.5
                        mobile:[&_p]:text-[11px] mobile:[&_p]:leading-[1.8]
                        mobile-type:[&_p]:text-[14px]"
                    >
                      <h2>Как рождается ваш маршрут</h2>
                      {ABOUT_FEATURES.map(({ Icon, title, text }) => (
                        <div key={title}>
                          <span
                            data-ui="soft-icon blue"
                            className={softBlueIconStyles}
                          >
                            <Icon size={21} />
                          </span>
                          <div>
                            <h3>{title}</h3>
                            <p>{text}</p>
                          </div>
                        </div>
                      ))}
                    </section>
                    <button
                      data-ui="about-link"
                      className="bg-white [border:1px_solid_var(--line)] rounded-[17px] flex items-center
                        justify-between gap-[15px] w-full p-[19px] mt-5 text-[#7a89a7] text-[11px]
                        text-left mobile:p-4 mobile:text-[11px] mobile-type:text-[12px]
                        [&_>_span]:flex [&_>_span]:gap-[11px] [&_>_span]:items-center
                        mobile:[&_>_span]:gap-[9px]"
                      onClick={() => setOnboarded(false)}
                    >
                      <span>
                        <Compass size={21} />
                        Посмотреть знакомство ещё раз
                      </span>
                      <ChevronRight size={19} />
                    </button>
                  </div>
                )}
              </>
            )}
          </main>
          {navVisible && (
            <nav
              data-ui="bottom-nav"
              className="fixed bottom-5 left-[50%] [transform:translateX(-50%)] z-[20] w-95 flex justify-around
                bg-[#fffffff2] [border:1px_solid_#e7eaf4] [box-shadow:0_8px_35px_#25305212]
                [backdrop-filter:blur(20px)] rounded-3xl py-2.5 px-[15px] mobile:left-0 mobile:right-0
                mobile:bottom-0 mobile:[transform:none] mobile:w-auto mobile:rounded-[23px_23px_0_0]
                mobile:bg-[#f8f9fc] mobile:pt-1.5 mobile:px-5 mobile:pb-[max(6px,_var(--app-safe-bottom))]
                mobile:[border-bottom:0] mobile:[border-left:0] mobile:[border-right:0]
                mobile:[box-shadow:0_-4px_25px_#30426b05] [&_button]:flex [&_button]:flex-col
                [&_button]:items-center [&_button]:justify-center [&_button]:gap-[5px]
                [&_button]:[background:none] [&_button]:text-[#969aab] [&_button]:min-w-22.5
                [&_button]:text-[11px] [&_button]:font-[650] [&_button]:p-1
                mobile:[&_button]:text-[11px] mobile:[&_button]:min-w-20 mobile:[&_button]:gap-[5px]
                mobile:[&_button]:min-h-11.5 [&_button_>_span]:relative [&_button_>_span]:flex
                [&_button_>_span]:items-center [&_button_>_span]:justify-center"
              aria-label="Основная навигация"
            >
              {(
                [
                  { value: "home", label: "Главная", Icon: House },
                  { value: "trips", label: "Мои поездки", Icon: Route },
                  { value: "about", label: "О сервисе", Icon: Compass },
                ] as const
              ).map(({ value, label, Icon }) => (
                <button
                  key={value}
                  data-ui={screen === value ? "active" : ""}
                  className={screen === value ? activeStyles : ""}
                  aria-current={screen === value ? "page" : undefined}
                  onClick={() => navigate(value)}
                >
                  <span>
                    <Icon
                      size={21}
                      strokeWidth={screen === value ? 2.3 : 1.7}
                    />
                    {screen === value && (
                      <motion.span
                        layoutId="nav-dot"
                        data-ui="nav-dot"
                        className="absolute -right-1.5 top-0 size-1 rounded-[50%] bg-brand"
                      />
                    )}
                  </span>
                  {label}
                </button>
              ))}
            </nav>
          )}
        </motion.div>
      )}
    </>
  );
}

function Loading({
  job,
  error,
  retry,
  onBack,
}: {
  job: Job | null;
  error: string;
  retry: () => void;
  onBack: () => void;
}) {
  const progress = job?.progress || 0;
  return (
    <div
      data-ui={`loading-page${error ? " has-error" : ""}`}
      className="max-w-120 text-center mt-2.5 mx-auto mb-10 mobile:mt-0 mobile:mx-auto mobile:mb-5 mobile:py-0
        mobile:px-1.5 [&_h1]:text-[34px] [&_h1]:font-extrabold [&_h1]:tracking-[-1.5px]
        [&_h1]:leading-[1.27] [&_h1]:my-[17px] [&_h1]:mx-0 mobile:[&_h1]:text-[29px]
        mobile:[&_h1]:tracking-[-1.2px] short:[&_h1]:my-3 short:[&_h1]:mx-0 [&_>_p]:text-[12px]
        [&_>_p]:leading-[1.9] [&_>_p]:text-muted mobile:[&_>_p]:text-[11px] [&_>_small]:block
        [&_>_small]:text-[11px] [&_>_small]:leading-[1.8] [&_>_small]:text-[#a6adbc]
        [&_>_small]:mt-[13px] mobile:[&_>_small]:text-[11px] mobile:[&_>_small]:leading-[1.9]
        [[data-ui~=screen-loading]_&]:w-full [[data-ui~=screen-loading]_&]:m-auto
        [[data-ui~=screen-loading]_&]:p-0
        [[data-ui~=screen-loading]_&_h1]:text-[clamp(25px,_4.5dvh,_34px)]
        [[data-ui~=screen-loading]_&_h1]:mt-2 [[data-ui~=screen-loading]_&_h1]:mx-0
        [[data-ui~=screen-loading]_&_h1]:mb-3 [[data-ui~=screen-loading]_&_>_p]:leading-[1.7]
        [[data-ui~=screen-loading]_&_>_small]:mt-2 [[data-ui~=screen-loading]_&_>_small]:leading-[1.6]"
    >
      <div
        data-ui="loading-visual"
        className="h-[245px] w-70 mt-0 mx-auto mb-[25px] relative grid place-items-center mobile:h-[235px]
          mobile:mb-[23px] short:[transform:scale(0.75)] short:-mt-7.5 short:-mb-3
          [[data-ui~=screen-loading]_&]:size-[clamp(110px,_21dvh,_210px)]
          [[data-ui~=screen-loading]_&]:mt-0 [[data-ui~=screen-loading]_&]:mx-auto
          [[data-ui~=screen-loading]_&]:mb-3 [[data-ui~=screen-loading]_&]:[transform:none]
          [[data-ui~=screen-loading]_[data-ui~=has-error]_&]:hidden"
      >
        <div
          data-ui="orbit orbit-one"
          className="absolute [border:1px_dashed_#dfe4f5] rounded-[50%] size-[225px]
            [[data-ui~=screen-loading]_&]:size-[90%]"
        />
        <div
          data-ui="orbit orbit-two"
          className="absolute [border:1px_dashed_#dfe4f5] rounded-[50%] size-[225px]
            [[data-ui~=orbit]&]:size-[159px] [[data-ui~=orbit]&]:border-solid
            [[data-ui~=orbit]&]:border-[#edf0fa]
            [[data-ui~=screen-loading]_[data-ui~=orbit]&]:size-[64%]"
        />
        <span
          data-ui="orbit-icon icon-weather"
          className="absolute grid place-items-center [border:5px_solid_#f8f9fc] size-[51px] rounded-[50%]
            [animation:bob_4s_ease-in-out_infinite] [[data-ui~=screen-loading]_&]:size-[24%]
            [[data-ui~=screen-loading]_&]:[border-width:3px]
            [[data-ui~=screen-loading]_&_>_svg]:size-[58%] top-3 right-[41px] bg-[#fff0d8]
            text-[#dba962] [[data-ui~=screen-loading]_&]:top-[1%]
            [[data-ui~=screen-loading]_&]:right-[10%]"
        >
          <CloudSun size={25} />
        </span>
        <span
          data-ui="orbit-icon icon-pin"
          className="absolute grid place-items-center [border:5px_solid_#f8f9fc] size-[51px] rounded-[50%]
            [animation:bob_4s_ease-in-out_infinite] [[data-ui~=screen-loading]_&]:size-[24%]
            [[data-ui~=screen-loading]_&]:[border-width:3px]
            [[data-ui~=screen-loading]_&_>_svg]:size-[58%] left-3 top-25.5 bg-[#e5ede5] text-[#7b9a79]
            [animation-delay:-1.4s] [[data-ui~=screen-loading]_&]:top-[40%]
            [[data-ui~=screen-loading]_&]:left-0"
        >
          <MapPin size={24} />
        </span>
        <span
          data-ui="orbit-icon icon-heart"
          className="absolute grid place-items-center [border:5px_solid_#f8f9fc] size-[51px] rounded-[50%]
            [animation:bob_4s_ease-in-out_infinite] [[data-ui~=screen-loading]_&]:size-[24%]
            [[data-ui~=screen-loading]_&]:[border-width:3px]
            [[data-ui~=screen-loading]_&_>_svg]:size-[58%] bottom-[11px] right-[61px] bg-[#f6e8ed]
            text-[#d695ac] [animation-delay:-2.3s] [[data-ui~=screen-loading]_&]:bottom-0
            [[data-ui~=screen-loading]_&]:right-[16%]"
        >
          <Heart size={21} />
        </span>
        <div
          data-ui="loading-compass"
          className="size-[109px] bg-[#ecf0ff] rounded-4xl text-brand grid place-items-center
            [box-shadow:0_10px_40px_#5065cf0c]
            [&_>_svg]:[animation:compass-turn_9s_ease-in-out_infinite]
            [[data-ui~=screen-loading]_&]:size-[45%] [[data-ui~=screen-loading]_&]:rounded-[28%]
            [[data-ui~=screen-loading]_&_>_svg]:size-[56%]"
        >
          <Compass size={59} strokeWidth={1.2} />
        </div>
      </div>
      <h1>
        Собираем день,
        <br />
        <span data-ui="blue-text" className="text-brand">
          который запомнится.
        </span>
      </h1>
      <p>
        Немного погоды, подходящая дорога
        <br />и места, которые могут стать любимыми.
      </p>
      <div
        data-ui="generation-progress"
        className="mt-8 mx-0 mb-6 text-left mobile:mt-[29px] short:my-5 short:mx-0 [&_>_div:first-child]:flex
          [&_>_div:first-child]:justify-between [&_>_div:first-child]:items-center
          [&_>_div:first-child]:gap-2.5 [&_>_div:first-child]:text-[11px]
          [&_>_div:first-child]:text-[#8b93a7] mobile:[&_>_div:first-child]:text-[11px]
          [&_strong]:text-brand [&_strong]:text-[12px] [[data-ui~=screen-loading]_&]:mt-4.5
          [[data-ui~=screen-loading]_&]:mx-0 [[data-ui~=screen-loading]_&]:mb-3
          [[data-ui~=screen-loading]_&_progress]:my-3 [[data-ui~=screen-loading]_&_progress]:mx-0"
      >
        <div>
          <span aria-live="polite">
            {job?.message || "Готовим всё к началу"}
          </span>
          <strong>{progress}%</strong>
        </div>
        <progress value={progress} max={100} aria-label="Прогресс генерации" />
        <div
          data-ui="generation-stages"
          className="flex justify-between gap-[7px] mobile-type:flex-wrap mobile-type:gap-2.5 [&_>_span]:flex
            [&_>_span]:items-center [&_>_span]:gap-[5px] [&_>_span]:text-[11px]
            [&_>_span]:text-[#aab1c1] mobile:[&_>_span]:text-[11px] mobile:[&_>_span]:gap-1
            mobile-type:[&_>_span]:text-[11px]"
        >
          {[
            [35, "Направление"],
            [62, "Погода и дорога"],
            [100, "Ваша программа"],
          ].map(([limit, label]) => (
            <span
              key={label}
              data-ui={progress >= Number(limit) ? "done" : ""}
              className={progress >= Number(limit) ? doneStyles : ""}
            >
              {progress >= Number(limit) ? (
                <Check size={13} />
              ) : (
                <span
                  data-ui="stage-dot"
                  className="size-[5px] rounded-[50%] bg-[#cdd3e1]"
                />
              )}
              {label}
            </span>
          ))}
        </div>
      </div>
      {error && (
        <>
          <Notice error>{error}</Notice>
          <Primary onClick={retry} id="retry-poll">
            Проверить ещё раз
          </Primary>
        </>
      )}
      <button
        data-ui="text-button"
        className={textButtonStyles}
        onClick={onBack}
      >
        Пока вернуться на главную <ArrowRight size={16} />
      </button>
      <small>
        Обычно занимает несколько минут. Можно обновить страницу —<br />
        мы постараемся восстановить статус.
      </small>
    </div>
  );
}
