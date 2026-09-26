import {
  emptyStateStyles,
  textButtonStyles,
} from "../ui-styles";
import { useEffect, useRef, useState } from "react";
import { ChevronRight, LoaderCircle, MapPin } from "lucide-react";
import { api, dateLabel, money, safeUrl } from "../lib";
import type { TripPlan } from "../types";
import { Notice, Primary } from "./UI";

interface Summary {
  id: string;
  destination_photo?: TripPlan["destination_photo"];
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
        <div role="status" aria-label="Загрузка поездок" className="grid gap-[16px] min-[760px]:grid-cols-2">
          {[0, 1, 2].map((index) => (
            <div
              key={index}
              aria-hidden="true"
              className="overflow-hidden rounded-[22px] border border-solid border-[var(--line)] bg-white motion-safe:animate-pulse"
            >
              <div className="h-[144px] bg-[#eff3ff]" />
              <div className="space-y-[12px] p-[20px] mobile:p-[14px]">
                <div className="h-[12px] w-24 rounded bg-[#eff3ff]" />
                <div className="h-[20px] w-3/4 rounded bg-[#eff3ff]" />
                <div className="h-[12px] w-1/2 rounded bg-[#eff3ff]" />
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="grid items-start gap-[16px] min-[760px]:grid-cols-2">
        {page?.items.map((item) => (
          <button
            key={item.id}
            data-ui="saved-trip"
            className="group flex w-full flex-col overflow-hidden rounded-[22px] border border-solid border-[var(--line)] bg-white p-0 text-left transition-[border-color,box-shadow] duration-200 hover:border-[#cbd5ed] hover:shadow-[0_6px_24px_#263b6410] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand"
            disabled={busy}
            aria-busy={openingId === item.id}
            onClick={() => void load(item.id)}
          >
            <TripCover photo={item.destination_photo} />
            <div className="flex w-full flex-1 flex-col p-[20px] mobile:p-[14px]">
              <small className="block text-[11px] font-medium leading-[16px] text-[#8e9bb2]">
                {dateLabel(item.start_date)}
              </small>
              <h2 className="mt-[8px] mb-[14px] text-[17px] font-bold leading-[1.45] tracking-[-0.4px] text-[#252b3d] [overflow-wrap:anywhere] mobile:text-[16px]">
                {item.title}
              </h2>
              <div className="mt-auto flex items-center justify-between gap-[12px] border-0 border-t border-solid border-[#edf0f6] pt-[14px]">
                <span className="text-[12px] leading-[18px] text-[#8e9bb2]">
                  {item.travelers} чел.
                  <span className="mx-[8px] text-[#c7cedc]">·</span>
                  <span className="font-semibold text-[#52617a]">
                    ≈ {money(item.estimated_total_rub)}
                  </span>
                </span>
                {openingId === item.id ? (
                  <LoaderCircle
                    size={18}
                    role="status"
                    aria-label="Открываем поездку"
                    className="shrink-0 text-brand motion-safe:animate-spin"
                  />
                ) : (
                  <ChevronRight size={18} className="shrink-0 text-[#99a8c1]" />
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
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

function TripCover({ photo }: { photo: TripPlan["destination_photo"] }) {
  const [failed, setFailed] = useState(false);
  const url = photo && safeUrl(photo.url);
  if (!url || failed) return null;

  return (
    <span data-ui="trip-cover" className="relative block h-[144px] w-full shrink-0 overflow-hidden bg-[#eff3ff]">
      <img
        src={url}
        alt=""
        title={`Фото: ${photo.author}`}
        loading="lazy"
        decoding="async"
        className="h-full w-full object-cover"
        onError={() => setFailed(true)}
      />
      <span className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/10 to-transparent" />
    </span>
  );
}
