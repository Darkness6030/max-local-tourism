import {
  emptyStateStyles,
  softBlueIconStyles,
  textButtonStyles,
} from "../ui-styles";
import { useEffect, useRef, useState } from "react";
import { ChevronRight, LoaderCircle, MapPin, Route } from "lucide-react";
import { api, dateLabel, money } from "../lib";
import type { TripPlan } from "../types";
import { Notice, Primary } from "./UI";

interface Summary {
  id: string;
  title: string;
  start_date: string;
  travelers: number;
  estimated_total_rub: number;
}
interface Page {
  items: Summary[];
  next_cursor: string | null;
  total: number;
}

export function MyTrips({
  initData,
  onOpen,
  onCreate,
}: {
  initData: string;
  onOpen: (plan: TripPlan) => void;
  onCreate: () => void;
}) {
  const [page, setPage] = useState<Page | null>(null);
  const [busy, setBusy] = useState(true);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const controller = useRef<AbortController | null>(null);
  const lock = useRef(false);

  useEffect(() => {
    const abort = new AbortController();
    controller.current = abort;
    lock.current = true;
    setBusy(true);
    setError("");
    api<Page>("/trips", initData, { signal: abort.signal })
      .then(setPage)
      .catch((err) => {
        if (!abort.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!abort.signal.aborted) {
          setBusy(false);
          lock.current = false;
        }
      });
    return () => abort.abort();
  }, [initData, retry]);

  async function load(id?: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setOpeningId(id ?? null);
    setError("");
    const signal = controller.current?.signal;
    try {
      if (id) {
        const plan = await api<TripPlan>(
          `/trips/${encodeURIComponent(id)}`,
          initData,
          { signal },
        );
        if (!signal?.aborted) onOpen(plan);
      } else if (page?.next_cursor) {
        const next = await api<Page>(
          `/trips?cursor=${encodeURIComponent(page.next_cursor)}`,
          initData,
          { signal },
        );
        if (!signal?.aborted)
          setPage({ ...next, items: [...page.items, ...next.items] });
      }
    } catch (err) {
      if (!signal?.aborted) setError((err as Error).message);
    } finally {
      if (!signal?.aborted) {
        setBusy(false);
        setOpeningId(null);
        lock.current = false;
      }
    }
  }

  return (
    <>
      {error && (
        <Notice error>
          {error}
          <button
            data-ui="text-button"
            className={textButtonStyles}
            onClick={() => setRetry((v) => v + 1)}
          >
            Обновить поездки
          </button>
        </Notice>
      )}
      {busy && !page && (
        <div role="status" aria-label="Загрузка поездок" className="space-y-[12px]">
          {[0, 1, 2].map((index) => (
            <div
              key={index}
              aria-hidden="true"
              className="flex items-center gap-[17px] rounded-[22px] border border-solid border-[var(--line)] bg-white p-[24px] motion-safe:animate-pulse mobile:gap-[13px] mobile:rounded-[22px] mobile:p-[18px]"
            >
              <span className="h-[48px] w-[48px] shrink-0 rounded-[15px] bg-[#eff3ff]" />
              <div className="flex-1 space-y-[10px]">
                <div className="h-[12px] w-24 rounded bg-[#eff3ff]" />
                <div className="h-[20px] w-3/4 rounded bg-[#eff3ff]" />
                <div className="h-[12px] w-1/2 rounded bg-[#eff3ff]" />
              </div>
            </div>
          ))}
        </div>
      )}
      {page?.items.map((item) => (
        <button
          key={item.id}
          data-ui="saved-trip"
          className={
            "w-full flex gap-[17px] items-center text-left p-[24px] [background:white] [border:1px_solid_var(--line)] rounded-[22px] mobile:p-[18px] mobile:gap-[13px] [&_>_div]:[flex:1] [&_>_div]:min-w-0 [&_>_div]:[overflow-wrap:anywhere] [&_small]:text-[11px] [&_small]:text-[#9ba6b9] mobile:[&_small]:text-[11px] [&_h2]:text-[18px] [&_h2]:leading-[1.5] [&_h2]:tracking-[-0.5px] [&_h2]:mt-[6px] [&_h2]:mx-0 [&_h2]:mb-[9px] [&_h2]:[font-weight:750] mobile:[&_h2]:text-[14px] mobile:[&_h2]:mt-[5px] mobile:[&_h2]:mx-0 mobile:[&_h2]:mb-[8px] [&_>_div_>_span]:text-[11px] [&_>_div_>_span]:text-[#8e9bb2] mobile:[&_>_div_>_span]:text-[11px] [&_>_svg]:text-[#a0afc8] mobile:[&_>_svg]:h-[17px] mobile:[&_>_svg]:w-[17px] [[data-ui~=saved-trip]_+_&]:mt-[12px]"
          }
          disabled={busy}
          aria-busy={openingId === item.id}
          onClick={() => void load(item.id)}
        >
          <span data-ui="soft-icon blue" className={softBlueIconStyles}>
            <Route size={25} />
          </span>
          <div className="flex flex-col items-start">
            <small className="block leading-[16px]">
              {dateLabel(item.start_date)}
            </small>
            <h2>{item.title}</h2>
            <span className="block leading-[16px]">
              {item.travelers} чел. · ≈ {money(item.estimated_total_rub)}
            </span>
          </div>
          {openingId === item.id ? (
            <LoaderCircle
              size={20}
              role="status"
              aria-label="Открываем поездку"
              className="shrink-0 motion-safe:animate-spin"
            />
          ) : (
            <ChevronRight size={20} />
          )}
        </button>
      ))}
      {busy && page && !openingId && (
        <div role="status" aria-label="Загрузка поездок" className="flex justify-center py-[16px] text-brand">
          <LoaderCircle size={22} aria-hidden="true" className="motion-safe:animate-spin" />
        </div>
      )}
      {page?.next_cursor && (
        <button
          data-ui="text-button"
          className={textButtonStyles}
          disabled={busy}
          onClick={() => void load()}
        >
          Показать ещё
        </button>
      )}
      {!busy && !error && page?.items.length === 0 && (
        <div data-ui="empty-state" className={emptyStateStyles}>
          <div
            data-ui="empty-orbit"
            className="h-[112px] w-[112px] grid place-items-center [border:1px_dashed_#d3dcf3] [background:#eff3ff] text-[#8b9fe2] rounded-[50%] mt-0 mx-0 mb-[27px] [[data-ui~=trips-page]_&]:w-[clamp(64px,_12dvh,_96px)] [[data-ui~=trips-page]_&]:h-[clamp(64px,_12dvh,_96px)] [[data-ui~=trips-page]_&]:mb-[16px]"
          >
            <MapPin size={39} />
          </div>
          <h2>Ваши открытия ещё впереди</h2>
          <p>
            Соберите первый маршрут — и он появится здесь. Даже один день может
            стать приключением.
          </p>
          <Primary onClick={onCreate}>Придумать поездку</Primary>
        </div>
      )}
    </>
  );
}
