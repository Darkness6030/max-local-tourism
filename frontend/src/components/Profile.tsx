import { useRef, useState } from "react";
import { ArrowLeft, Check, ChevronDown } from "lucide-react";
import type { AppConfig, Identity, ProfilePreferences, UserProfile } from "../types";
import { api } from "../lib";
import { defaultProfilePreferences, profileColors, profileInterests } from "../profile";
import { avatarStyles, eyebrowStyles, fieldLabelStyles, iconButtonStyles, tripsPageStyles } from "../ui-styles";
import { ProfileAvatar } from "./ProfileAvatar";
import { Primary } from "./UI";

const panel = "rounded-[22px] border border-[#e4e8f1] bg-white p-5 mobile:p-4";

export function Profile({ user, profile, config, initData, onBack, onSave }: {
  user: Identity["user"]; profile: UserProfile; config: AppConfig; initData: string;
  onBack: () => void; onSave: (profile: UserProfile) => void;
}) {
  const [values, setValues] = useState<ProfilePreferences>({ ...defaultProfilePreferences, ...profile.preferences });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const lock = useRef(false);
  const update = (patch: Partial<ProfilePreferences>) => { setValues((old) => ({ ...old, ...patch })); setSaved(false); };
  const color = profileColors[values.avatar_color];
  const save = async () => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const next = await api<UserProfile>("/profile", initData, { method: "PUT", body: JSON.stringify(values) });
      setValues(next.preferences ?? defaultProfilePreferences); onSave(next); setSaved(true);
    } catch (reason) { setError((reason as Error).message); }
    finally { lock.current = false; setBusy(false); }
  };
  return <div data-ui="profile-page" className={tripsPageStyles}>
    <div className="flex items-center gap-3 mb-5">
      <button className={iconButtonStyles} onClick={onBack} aria-label="Назад из профиля"><ArrowLeft size={21} /></button>
      <span className={eyebrowStyles}>ВАШЕ МЕСТО В «РЯДОМ»</span>
    </div>
    <h1 className="mb-3">Профиль</h1>
    <p className="text-muted text-[14px] leading-[1.7] mb-6">Немного о вас — чтобы каждая поездка была ближе.</p>
    <form onSubmit={(event) => { event.preventDefault(); void save(); }} className="grid gap-4">
      <fieldset disabled={busy} className={`${panel} min-w-0 grid gap-5`}>
        <legend className="sr-only">Имя и аватар</legend>
        <div className="flex items-center gap-4">
          <span data-ui="profile-preview avatar" className={`${avatarStyles} !size-18 !text-[24px] shrink-0`}
            style={{ background: color.background, color: color.color }}>
            <ProfileAvatar user={user} preferences={values} />
          </span>
          <div className="min-w-0"><strong className="block text-[18px] break-words">{values.display_name.trim() || user.first_name}</strong>
            <span className="text-muted text-[12px]">Ваш профиль путешественника</span></div>
        </div>
        <label className={fieldLabelStyles}>Имя в приложении
          <input name="display_name" maxLength={60} value={values.display_name} placeholder={user.first_name}
            onChange={(e) => update({ display_name: e.target.value })} />
        </label>
        <div><h2 className="text-[14px] font-bold mb-3">Аватар</h2>
          <div className="flex flex-wrap gap-2">
            {([['max', 'Фото MAX'], ['initials', 'Инициалы'], ['compass', 'Компас'], ['mountain', 'Горы'], ['sun', 'Солнце']] as const).map(([value, label]) =>
              <button type="button" key={value} aria-pressed={values.avatar_style === value}
                className={`px-3 py-2 rounded-xl border text-[12px] ${values.avatar_style === value ? 'bg-[#edf0ff] border-brand text-brand' : 'bg-white border-[#e4e8f1] text-muted'}`}
                onClick={() => update({ avatar_style: value })}>{label}</button>)}
          </div>
        </div>
        <div><h2 className="text-[14px] font-bold mb-3">Цвет аватара</h2>
          <div className="flex gap-3">{Object.entries(profileColors).map(([value, shade]) =>
            <button type="button" key={value} aria-label={shade.name} aria-pressed={values.avatar_color === value}
              className="size-11 rounded-full flex items-center justify-center border border-[#dce1ec]"
              style={{ background: shade.background, color: shade.color }}
              onClick={() => update({ avatar_color: value as ProfilePreferences['avatar_color'] })}>
              {values.avatar_color === value && <Check size={19} />}
            </button>)}</div>
        </div>
      </fieldset>
      <fieldset disabled={busy} className={`${panel} min-w-0 grid gap-5`}>
        <legend className="sr-only">Предпочтения для поездок</legend>
        <div><h2 className="text-[17px] font-bold">Поездки по вашему вкусу</h2>
          <p className="text-muted text-[12px] leading-[1.7] mt-1">Эти настройки подставятся в анкету. Перед поездкой их можно изменить.</p></div>
        <label className={`${fieldLabelStyles} relative`}>Город отправления
          <select className="appearance-none !pr-10" name="origin" aria-label="Город отправления" value={values.origin} onChange={(e) => update({ origin: e.target.value })}>
            {config.origins.map((city) => <option key={city}>{city}</option>)}
          </select><ChevronDown size={18} aria-hidden="true" className="absolute right-3.5 bottom-4.5 pointer-events-none text-muted" /></label>
        <label className={`${fieldLabelStyles} relative`}>Темп поездок
          <select className="appearance-none !pr-10" name="pace" aria-label="Темп поездок" value={values.pace} onChange={(e) => update({ pace: e.target.value as ProfilePreferences['pace'] })}>
            <option value="relaxed">Без спешки</option><option value="balanced">Всего понемногу</option><option value="intensive">Больше впечатлений</option>
          </select><ChevronDown size={18} aria-hidden="true" className="absolute right-3.5 bottom-4.5 pointer-events-none text-muted" /></label>
        <div><h2 className="text-[14px] font-bold mb-3">Что вам интересно</h2>
          <div className="flex flex-wrap gap-2">{profileInterests.map((interest) => <button type="button" key={interest}
            aria-pressed={values.interests.includes(interest)} className={`px-3 py-2 rounded-xl border text-[12px] ${values.interests.includes(interest) ? 'bg-[#edf0ff] border-brand text-brand' : 'bg-white border-[#e4e8f1] text-muted'}`}
            onClick={() => update({ interests: values.interests.includes(interest) ? values.interests.filter((value) => value !== interest) : [...values.interests, interest] })}>{interest}</button>)}</div>
        </div>
      </fieldset>
      {error && <p role="alert" className="text-red-700 text-[13px]">{error}</p>}
      {saved && <p role="status" className="text-brand text-[13px]">Настройки сохранены.</p>}
      <Primary type="submit" busy={busy} arrow={false}>{busy ? "Сохраняем…" : "Сохранить настройки"}</Primary>
    </form>
  </div>;
}
