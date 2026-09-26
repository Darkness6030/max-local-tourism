import { ArrowDown, ArrowUpRight, Check, Compass, MapPin, Route, Sparkles } from "lucide-react";
import journey from "../assets/journey.webp";
import { Brand, Notice } from "./UI";

const steps = [
  { Icon: Compass, title: "Расскажите о планах", text: "Откуда едем, с кем и что хочется увидеть." },
  { Icon: Sparkles, title: "Найдите свой маршрут", text: "Программа, погода и дорога — в одной поездке." },
  { Icon: Route, title: "Возьмите день с собой", text: "Сохраните план и позовите тех, с кем хорошо." },
];

const actionStyles = "inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-2xl px-4 py-3.5 text-[13px] font-bold no-underline";

export function MaxEntry({ botUrl, sharedTrip, error }: {
  botUrl: string;
  sharedTrip: boolean;
  error?: string;
}) {
  return (
    <div data-ui="max-entry" className="min-h-dvh overflow-x-clip">
      <header className="mx-auto flex max-w-280 items-center justify-between px-6 py-7 mobile:py-5">
        <Brand />
        <span className="text-[11px] text-muted mobile:hidden">Маленькие путешествия. Большие впечатления.</span>
      </header>
      <main className="mx-auto max-w-280 px-6 pb-10 mobile:px-5">
        <section
          aria-labelledby="max-entry-title"
          className="grid grid-cols-2 items-center gap-12 py-8 tablet:gap-7 mobile:grid-cols-1 mobile:gap-8 mobile:pt-6"
        >
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-[#eaf0ff] px-3 py-2 text-[10px] font-extrabold tracking-wider text-brand">
              <span className="size-1.5 rounded-full bg-brand" />
              {sharedTrip ? "ВАМ ПРИСЛАЛИ МАРШРУТ" : "ВАШ СЛЕДУЮЩИЙ ХОРОШИЙ ДЕНЬ"}
            </span>
            <h1 id="max-entry-title" className="mt-6 text-[48px] font-extrabold leading-[1.12] tracking-[-2px] tablet:text-[40px] mobile:mt-5 mobile:text-[36px] narrow:text-[32px]">
              {sharedTrip ? <>Новые впечатления<br /><span className="text-brand">уже ждут вас.</span></> : <>Сменить обстановку.<br /><span className="text-brand">Остаться рядом.</span></>}
            </h1>
            <p className="mt-5 max-w-100 text-[14px] leading-[1.9] text-[#687389] mobile:mt-4">
              {sharedTrip
                ? "Откройте «Рядом» в MAX — маршрут сохранится в ваших поездках и откроется после входа."
                : "Интересные места, неспешные прогулки и новые впечатления. Соберите свой маленький отпуск на один выходной."}
            </p>
            <div className="mt-7 max-w-100 rounded-2xl border border-solid border-[#e5eaf6] bg-white/70 p-4">
              <div className="flex items-center gap-2 text-[13px] font-bold text-ink">
                <Compass size={18} className="text-brand" />
                Путешествие начинается в MAX
              </div>
              <p className="mt-2 text-[12px] leading-[1.8] text-muted">Войдите через свой профиль, чтобы маршруты всегда были под рукой.</p>
            </div>
            <div data-ui="max-entry-actions" className="mt-5 grid max-w-100 grid-cols-2 gap-3 mobile:grid-cols-1">
              <a href={botUrl} className={`${actionStyles} bg-brand text-white shadow-lg shadow-brand/15 hover:bg-[#3049d7]`}>
                Открыть в MAX <ArrowUpRight size={18} />
              </a>
              <a href="#how-it-works" className={`${actionStyles} bg-[#eaf0ff] text-brand hover:bg-[#dfe7ff]`}>
                Как это работает <ArrowDown size={16} />
              </a>
            </div>
            {error && <div className="mt-4 max-w-100"><Notice>{error}</Notice></div>}
          </div>
          <div className="relative min-w-0 py-4 mobile:py-0" aria-hidden="true">
            <div className="absolute -right-8 -top-2 size-64 rounded-full bg-[#e7ecff] mobile:size-40" />
            <div className="relative overflow-hidden rounded-[32px] bg-[#dfe9e2] shadow-xl shadow-[#263c52]/10">
              <img src={journey} alt="" className="h-130 w-full object-cover object-[60%_center] tablet:h-120 mobile:h-72" />
              <div className="absolute inset-0 bg-linear-to-t from-[#183633]/95 via-[#183633]/40 to-transparent" />
              <div className="absolute left-6 right-6 top-6 flex items-center justify-between gap-3">
                <span className="inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-2 text-[11px] font-bold text-[#436256]">
                  <MapPin size={14} /> Где-то совсем рядом
                </span>
                <span className="grid size-10 shrink-0 place-items-center rounded-full border border-solid border-white/50 bg-white/20 text-white backdrop-blur-md">
                  <Compass size={22} />
                </span>
              </div>
              <div className="absolute bottom-16 left-7 right-7 text-white mobile:left-5">
                <p className="text-[10px] font-bold tracking-[2px] text-white/75">МЕНЬШЕ СУЕТЫ. БОЛЬШЕ ОТКРЫТИЙ.</p>
                <p className="mt-3 text-[32px] font-extrabold leading-tight tracking-[-1px] mobile:text-[26px]">Хороший день<br />ближе, чем кажется.</p>
              </div>
            </div>
            <div className="absolute -bottom-2 left-6 right-6 flex items-center gap-3 rounded-2xl border border-solid border-[#e7ece9] bg-white px-4 py-3 shadow-lg shadow-[#263c52]/5 mobile:-bottom-5">
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-[#eaf2e7] text-[#6a8964]"><Check size={19} /></span>
              <span className="text-[12px] font-bold text-ink">Весь маршрут — в одном месте</span>
              <Route size={18} className="ml-auto text-[#91a78b]" />
            </div>
          </div>
        </section>
        <section id="how-it-works" aria-labelledby="how-it-works-title" className="scroll-mt-6 border-0 border-t border-solid border-[#e5e9f2] pt-8 mt-9 mobile:mt-12">
          <h2 id="how-it-works-title" className="text-[21px] font-extrabold tracking-tight">От «куда бы выбраться» до «поехали»</h2>
          <div className="mt-6 grid grid-cols-3 gap-7 mobile:grid-cols-1 mobile:gap-6">
            {steps.map(({ Icon, title, text }, index) => (
              <div key={title} className="flex items-start gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#eaf0ff] text-brand"><Icon size={20} /></span>
                <div>
                  <h3 className="text-[13px] font-bold leading-6"><span className="mr-1 text-muted">0{index + 1}.</span> {title}</h3>
                  <p className="mt-1 text-[12px] leading-[1.8] text-muted">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
