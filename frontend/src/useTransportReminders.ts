import { useEffect, useRef, useState } from "react";
import { api } from "./lib";

export type ReminderDirection = "outbound" | "return_trip";
type ReminderState = { outbound: number | null; return_trip: number | null; available: boolean };

export function useTransportReminders(tripId: string, initData: string) {
  const [state, setState] = useState<ReminderState | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const generation = useRef(0);
  const inFlight = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    generation.current += 1;
    inFlight.current = false;
    setState(null);
    setSaving(false);
    setError("");
    api<ReminderState>(`/trips/${tripId}/reminders`, initData, { signal: controller.signal })
      .then((value) => { if (!controller.signal.aborted) setState(value); })
      .catch(() => { if (!controller.signal.aborted) setError("Не удалось загрузить напоминания."); });
    return () => { controller.abort(); generation.current += 1; };
  }, [tripId, initData, retry]);

  const toggle = async (direction: ReminderDirection, index: number) => {
    if (!state || !state.available || inFlight.current) return;
    const current = generation.current;
    inFlight.current = true;
    setSaving(true);
    setError("");
    try {
      const value = await api<ReminderState>(`/trips/${tripId}/reminders/${direction}`, initData, {
        method: "PUT",
        body: JSON.stringify({ option_index: state[direction] === index ? null : index }),
      });
      if (current === generation.current) setState(value);
    } catch (reason) {
      if (current !== generation.current) return;
      setError(reason instanceof Error ? reason.message : "Не удалось сохранить напоминание.");
      // A timed-out request may still have committed. Read back before another choice.
      try {
        const value = await api<ReminderState>(`/trips/${tripId}/reminders`, initData);
        if (current === generation.current) setState(value);
      } catch {
        if (current === generation.current) setState(null);
      }
    } finally {
      if (current === generation.current) {
        inFlight.current = false;
        setSaving(false);
      }
    }
  };
  return { state, saving, error, toggle, retry: () => setRetry((value) => value + 1) };
}
