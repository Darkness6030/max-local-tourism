import { eyebrowStyles } from "../ui-styles";
import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowUpRight,
  Check,
  CloudSun,
  Heart,
  MapPin,
  Route,
  Sparkles,
  Users,
  Wallet,
} from "lucide-react";
import journey from "../assets/journey.webp";
import { Brand, Primary } from "./UI";

const slides = [
  {
    eyebrow: "МАЛЕНЬКИЕ ПУТЕШЕСТВИЯ",
    title: (
      <>
        Большие впечатления.
        <br />
        <span>Где-то рядом.</span>
      </>
    ),
    description:
      "Чтобы сменить обстановку, не нужен отпуск. Иногда достаточно одного свободного дня.",
  },
  {
    eyebrow: "ПО ВАШИМ ПРАВИЛАМ",
    title: (
      <>
        Ваше настроение.
        <br />
        <span>Ваш маршрут.</span>
      </>
    ),
    description:
      "Неспешная прогулка или день открытий? Расскажите, чего хочется, а детали мы соберём вместе.",
  },
  {
    eyebrow: "ОТ ИДЕИ ДО ПОЕЗДКИ",
    title: (
      <>
        Меньше планировать.
        <br />
        <span>Больше проживать.</span>
      </>
    ),
    description:
      "Программа, погода, дорога и бюджет — в одном месте. Остаётся позвать тех, с кем хорошо.",
  },
];

export function Onboarding({ onDone }: { onDone: () => void }) {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const change = (next: number) => {
    if (next >= 0 && next < slides.length) {
      setDirection(next > index ? 1 : -1);
      setIndex(next);
    }
  };
  const slide = slides[index];
  return (
    <div
      data-ui="onboarding"
      className="max-w-[1060px] h-[100dvh] m-auto pt-0 px-0 pb-[max(12px,_env(safe-area-inset-bottom))] flex flex-col desktop-fit:mx-[35px] mobile:m-0 mobile:pt-0 mobile:px-[22px] mobile:pb-[max(12px,_env(safe-area-inset-bottom))] narrow:px-[18px]"
      onKeyDown={(event) => {
        if (event.key === "ArrowRight") change(index + 1);
        if (event.key === "ArrowLeft") change(index - 1);
        if (event.key === "Escape") onDone();
      }}
    >
      <header
        data-ui="onboarding-header"
        className="h-[105px] shrink-0 flex items-center justify-between mobile:h-[78px] mobile:min-h-[78px] mobile:pt-[env(safe-area-inset-top)] short:h-[64px] short:min-h-[64px] short:shrink-0"
      >
        <Brand />
        <button
          data-ui="text-button muted"
          className={
            "inline-flex items-center justify-center gap-[8px] text-[12px] [font-weight:650] [background:transparent] text-brand py-[10px] px-[4px] [[data-ui~=onboarding-header]_&]:text-[12px] mobile:[[data-ui~=onboarding-header]_&]:text-[11px] [[data-ui~=result-hero]_>_&]:text-[11px] [[data-ui~=result-hero]_>_&]:min-h-[38px] mobile:[[data-ui~=result-hero]_>_&]:text-[11px] mobile:[[data-ui~=result-hero]_>_&]:mt-[4px] [[data-ui~=train-bottom]_>_&]:text-[11px] mobile:[[data-ui~=train-bottom]_>_&]:text-[11px] mobile-type:[[data-ui~=train-bottom]_>_&]:text-[12px] text-muted [[data-ui~=text-button]&]:text-muted"
          }
          onClick={onDone}
        >
          Пропустить
          <span
            data-ui="sr-only"
            className="absolute w-[1px] h-[1px] p-0 m-[-1px] overflow-hidden [clip:rect(0,_0,_0,_0)] whitespace-nowrap [border:0]"
          >
            {" "}
            знакомство
          </span>
        </button>
      </header>
      <div
        data-ui="onboarding-body"
        className="[flex:1] min-h-0 [overflow-y:auto] [overflow-x:clip] py-[12px] px-0 flex flex-col mobile:pt-[7px] mobile:px-0 mobile:pb-[12px] short:py-[12px] short:px-0 short-mobile:pt-0 short-mobile:px-0 short-mobile:pb-[8px]"
      >
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={index}
            data-ui={`onboarding-slide slide-${index}`}
            className="shrink-0 my-auto mx-0 grid grid-cols-[1.08fr_1fr] gap-[65px] items-center tablet:gap-[35px] mobile:flex mobile:flex-col mobile:gap-0"
            initial={{ opacity: 0, x: direction * 32 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -24 }}
            transition={{ duration: 0.24 }}
          >
            <motion.div
              data-ui="onboarding-art"
              className={
                "h-[clamp(240px,_calc(100dvh_-_285px),_530px)] relative rounded-[34px] overflow-hidden [background:#dfebe6] [touch-action:pan-y] tablet:h-[clamp(240px,_calc(100dvh_-_285px),_490px)] mobile:h-[clamp(230px,_37dvh,_365px)] mobile:w-full mobile:rounded-[27px] mobile:shrink-0 narrow:h-[clamp(200px,_34dvh,_285px)] short:h-[max(240px,_calc(100dvh_-_225px))] short-mobile:h-[clamp(160px,_32dvh,_205px)] short-mobile:rounded-[22px] [&_>_img]:w-full [&_>_img]:h-full [&_>_img]:object-cover [&_>_img]:object-[61%_center] mobile:[&_>_img]:object-[64%_center]"
              }
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.12}
              onDragEnd={(_, info) => {
                if (Math.abs(info.offset.x) > 55)
                  change(index + (info.offset.x < 0 ? 1 : -1));
              }}
            >
              <img
                src={journey}
                alt="Иллюстрация маленького города у реки"
                draggable={false}
              />
              <span
                data-ui="art-shade"
                className="absolute top-[50%] right-0 bottom-0 left-0 [background:linear-gradient(transparent,_#23352045)]"
              />
              {index === 0 && (
                <>
                  <motion.div
                    data-ui="floating-label label-top"
                    className={
                      "absolute flex items-center gap-[7px] py-[11px] px-[14px] [background:#ffffffed] [backdrop-filter:blur(10px)] [box-shadow:0_5px_20px_#26343116] rounded-[15px] text-[11px] font-bold text-[#3d5241] mobile:text-[11px] mobile:py-[10px] mobile:px-[12px] mobile:gap-[6px] mobile:rounded-[12px] mobile:[&_>_svg]:h-[14px] mobile:[&_>_svg]:w-[14px] top-[29px] left-[24px] [transform:rotate(-5deg)] mobile:left-[17px] mobile:top-[20px]"
                    }
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                  >
                    <MapPin size={16} />
                    <span>Ближе, чем кажется</span>
                  </motion.div>
                  <div
                    data-ui="onboard-postcard"
                    className={
                      "absolute bottom-[30px] left-[25px] right-[25px] rounded-[20px] [background:#ffffffee] [backdrop-filter:blur(16px)] py-[17px] px-[15px] flex items-center gap-[12px] [box-shadow:0_10px_25px_#17362016] mobile:left-[16px] mobile:right-[16px] mobile:bottom-[25px] mobile:rounded-[16px] mobile:py-[14px] mobile:px-[12px] mobile:gap-[9px] narrow-type:gap-[8px] narrow-type:p-[13px] [&_>_span:nth-child(2)]:[flex:1] [&_small]:text-[11px] [&_small]:text-muted [&_small]:tracking-[1px] [&_small]:block [&_small]:mb-[4px] mobile:[&_small]:text-[11px] mobile-type:[&_small]:text-[9px] mobile-type:[&_small]:tracking-[0.3px] [&_strong]:text-[12px] [&_strong]:[font-weight:750] mobile:[&_strong]:text-[11px] narrow-type:[&_strong]:text-[12px] [&_>_svg]:text-brand mobile:[&_>_svg]:h-[18px] mobile:[&_>_svg]:w-[18px]"
                    }
                  >
                    <span
                      data-ui="postcard-icon"
                      className="w-[44px] h-[44px] grid place-items-center rounded-[13px] [background:#e9edff] text-brand mobile:h-[36px] mobile:w-[36px] mobile:rounded-[11px] mobile:[&_svg]:h-[21px] mobile:[&_svg]:w-[21px]"
                    >
                      <CompassArt />
                    </span>
                    <span>
                      <small>ПЛАН НА ВЫХОДНЫЕ</small>
                      <strong>Открыть что-то новое</strong>
                    </span>
                    <ArrowUpRight size={21} />
                  </div>
                </>
              )}
              {index === 1 && (
                <div
                  data-ui="preference-float"
                  className="absolute bottom-[37px] left-[29px] right-[29px] [background:#fffc] [border:1px_solid_#fff9] p-[21px] rounded-[24px] [backdrop-filter:blur(20px)] [box-shadow:0_16px_30px_#183b3920] [transform:rotate(-3deg)] mobile:bottom-[30px] mobile:left-[22px] mobile:right-[22px] mobile:p-[16px] mobile:rounded-[18px] short-mobile:bottom-[14px] short-mobile:p-[12px]"
                >
                  <div
                    data-ui="preference-title"
                    className="flex gap-[10px] items-center mb-[13px] text-brand text-[14px] mobile:text-[12px] mobile:mb-[9px]"
                  >
                    <Sparkles size={19} />
                    <strong>Идеально для вас</strong>
                  </div>
                  {[
                    [Heart, "Местная кухня и прогулки"],
                    [Users, "Вдвоём, без спешки"],
                    [Wallet, "В рамках вашего бюджета"],
                  ].map(([Icon, text]) => {
                    const Glyph = Icon as typeof Heart;
                    return (
                      <div
                        data-ui="preference-row"
                        className={
                          "flex gap-[10px] items-center py-[12px] px-0 text-[11px] text-[#596478] mobile:text-[11px] mobile:py-[10px] mobile:px-0 mobile:gap-[8px] short-mobile:py-[6px] [&_>_span:first-of-type]:[flex:1] mobile:[&_>_svg]:h-[16px] mobile:[&_>_svg]:w-[16px]"
                        }
                        key={text as string}
                      >
                        <Glyph size={18} />
                        <span>{text as string}</span>
                        <span
                          data-ui="mini-check"
                          className="w-[19px] h-[19px] [background:#e5ede2] text-[#487441] rounded-[50%] grid place-items-center"
                        >
                          <Check size={12} />
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
              {index === 2 && (
                <div
                  data-ui="onboard-timeline"
                  className={
                    "absolute left-[25px] right-[25px] bottom-[34px] py-[22px] px-[20px] [background:#fffef9f5] rounded-[23px] [box-shadow:0_10px_40px_#31392e20] [transform:rotate(2deg)] mobile:left-[18px] mobile:right-[18px] mobile:bottom-[27px] mobile:py-[18px] mobile:px-[15px] short-mobile:bottom-[14px] short-mobile:p-[12px] [&_>_div:not(:first-child)]:flex [&_>_div:not(:first-child)]:gap-[10px] [&_>_div:not(:first-child)]:items-center [&_>_div:not(:first-child)]:text-[11px] [&_>_div:not(:first-child)]:py-[10px] [&_>_div:not(:first-child)]:px-0 mobile:[&_>_div:not(:first-child)]:text-[11px] mobile:[&_>_div:not(:first-child)]:gap-[8px] mobile:[&_>_div:not(:first-child)]:py-[8px] mobile:[&_>_div:not(:first-child)]:px-0 short-mobile:[&_>_div:not(:first-child)]:py-[6px] [&_time]:text-muted [&_time]:text-[11px] mobile:[&_time]:text-[11px] [&_>_small]:text-[11px] [&_>_small]:text-muted [&_>_small]:block [&_>_small]:[border-top:1px_solid_var(--line)] [&_>_small]:pt-[13px] [&_>_small]:mt-[7px] mobile:[&_>_small]:text-[11px] mobile:[&_>_small]:pt-[10px]"
                  }
                >
                  <div
                    data-ui="onboard-timeline-head"
                    className="flex items-center justify-between mb-[15px] text-[13px] mobile:text-[11px] mobile:mb-[10px] [&_svg]:text-[#e6a057]"
                  >
                    <strong>Ваш идеальный день</strong>
                    <CloudSun size={24} />
                  </div>
                  <div>
                    <time>10:30</time>
                    <span
                      data-ui="tiny-dot"
                      className="w-[6px] h-[6px] rounded-[50%] [background:var(--blue)]"
                    />
                    <span>Затеряться в старом городе</span>
                  </div>
                  <div>
                    <time>13:00</time>
                    <span
                      data-ui="tiny-dot"
                      className="w-[6px] h-[6px] rounded-[50%] [background:var(--blue)]"
                    />
                    <span>Попробовать что-то местное</span>
                  </div>
                  <div>
                    <time>15:30</time>
                    <span
                      data-ui="tiny-dot"
                      className="w-[6px] h-[6px] rounded-[50%] [background:var(--blue)]"
                    />
                    <span>Никуда не торопиться</span>
                  </div>
                  <small>Пример программы · время подберём для вас</small>
                </div>
              )}
            </motion.div>
            <div
              data-ui="onboarding-copy"
              className="pb-0 mobile:pt-[28px] mobile:px-[4px] mobile:pb-0 mobile:text-center mobile:w-full short-mobile:pt-[16px] [&_h1]:text-[38px] [&_h1]:font-extrabold [&_h1]:tracking-[-1.7px] [&_h1]:leading-[1.24] [&_h1]:my-[20px] [&_h1]:mx-0 tablet:[&_h1]:text-[31px] mobile:[&_h1]:text-[28px] mobile:[&_h1]:leading-[1.26] mobile:[&_h1]:tracking-[-1.15px] mobile:[&_h1]:my-[13px] mobile:[&_h1]:mx-0 narrow:[&_h1]:text-[25px] short-mobile:[&_h1]:text-[clamp(24px,_6.2vw,_28px)] short-mobile:[&_h1]:my-[9px] short-mobile:[&_h1]:mx-0 [&_h1_span]:text-brand [&_p]:text-[14px] [&_p]:leading-[1.9] [&_p]:max-w-[350px] mobile:[&_p]:text-[11px] mobile:[&_p]:leading-[1.9] mobile:[&_p]:max-w-[290px] mobile:[&_p]:my-0 mobile:[&_p]:mx-auto narrow:[&_p]:text-[11px] mobile-type:[&_p]:text-[14px] narrow-type:[&_p]:text-[13px] [&_p]:text-[#687389] short-mobile:[&_p]:max-w-[350px] short-mobile:[&_p]:leading-[1.65]"
            >
              <span data-ui="eyebrow" className={eyebrowStyles}>
                {slide.eyebrow}
              </span>
              <h1>{slide.title}</h1>
              <p>{slide.description}</p>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div
        data-ui="onboarding-controls"
        className="shrink-0 [align-self:flex-end] w-[calc((100%_-_65px)_/_2.08)] pt-[4px] tablet:w-[calc((100%_-_35px)_/_2.08)] mobile:w-full"
      >
        <div
          data-ui="pagination"
          className="flex justify-center gap-0 m-0"
          aria-label="Экраны знакомства"
        >
          {slides.map((_, i) => (
            <button
              key={i}
              type="button"
              className="group grid h-[44px] w-[32px] shrink-0 place-items-center rounded-full bg-transparent p-0 focus-visible:outline-2 focus-visible:outline-offset-[-4px] focus-visible:outline-brand"
              aria-label={`Экран знакомства ${i + 1}`}
              aria-current={i === index ? "step" : undefined}
              onClick={() => change(i)}
            >
              <span
                data-ui={i === index ? "active" : ""}
                aria-hidden="true"
                className={`block h-[6px] rounded-full transition-[width,background-color] duration-200 ease-out motion-reduce:transition-none ${
                  i === index
                    ? "w-[18px] bg-brand"
                    : "w-[6px] bg-[#cbd2e3] group-hover:bg-[#aab6d1]"
                }`}
              />
            </button>
          ))}
        </div>
        <Primary onClick={() => (index === 2 ? onDone() : change(index + 1))}>
          {index === 2 ? "Начать путешествие" : "Дальше"}
        </Primary>
      </div>
    </div>
  );
}
function CompassArt() {
  return <Route size={24} strokeWidth={1.7} />;
}
