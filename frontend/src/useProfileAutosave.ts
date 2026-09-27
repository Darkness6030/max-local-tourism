import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "./lib";
import type { ProfilePreferences, UserProfile } from "./types";

// Owned by App so navigation away from Profile cannot cancel a pending save.
export function useProfileAutosave(initData: string, onSaved: (profile: UserProfile) => void) {
  const [error, setError] = useState("");
  const onSavedRef = useRef(onSaved);
  onSavedRef.current = onSaved;
  const queue = useMemo(() => ({
    latest: null as { preferences: ProfilePreferences; version: number } | null,
    savedVersion: 0, running: false, closed: false, failures: 0,
    timer: undefined as ReturnType<typeof setTimeout> | undefined,
  }), [initData]);

  const flush = useCallback(async () => {
    clearTimeout(queue.timer);
    if (queue.closed || queue.running || !queue.latest || queue.latest.version === queue.savedVersion) return;
    const sent = queue.latest;
    queue.running = true;
    let retry = false;
    try {
      const result = await api<UserProfile>("/profile", initData, {
        method: "PUT", body: JSON.stringify(sent.preferences), keepalive: true,
      });
      if (queue.closed) return;
      queue.savedVersion = sent.version;
      queue.failures = 0;
      setError("");
      // Never let an older response replace edits made while the request was in flight.
      if (queue.latest.version === sent.version) onSavedRef.current(result);
    } catch (reason) {
      if (queue.closed) return;
      queue.failures += 1;
      retry = !(reason instanceof ApiError && reason.status && reason.status < 500 && reason.status !== 429);
      setError(retry
        ? "Не удалось сохранить настройки. Повторим автоматически, когда связь восстановится."
        : "Не удалось сохранить настройки. Обновите приложение и попробуйте ещё раз.");
    } finally {
      queue.running = false;
      if (!queue.closed && queue.latest && queue.latest.version !== queue.savedVersion) {
        if (queue.latest.version !== sent.version) void flush();
        else if (retry) queue.timer = setTimeout(() => void flush(), Math.min(2000 * 2 ** Math.min(queue.failures - 1, 4), 30000));
      }
    }
  }, [initData, queue]);

  const change = useCallback((preferences: ProfilePreferences) => {
    queue.latest = { preferences, version: (queue.latest?.version ?? 0) + 1 };
    queue.failures = 0;
    setError("");
    clearTimeout(queue.timer);
    queue.timer = setTimeout(() => void flush(), 400);
  }, [queue, flush]);

  useEffect(() => {
    queue.closed = false;
    setError("");
    const resume = () => { void flush(); };
    window.addEventListener("online", resume);
    window.addEventListener("pagehide", resume);
    return () => {
      queue.closed = true;
      clearTimeout(queue.timer);
      window.removeEventListener("online", resume);
      window.removeEventListener("pagehide", resume);
    };
  }, [queue, flush]);

  return { change, flush, error };
}
