import { useEffect } from "react";
import { ChevronDown } from "lucide-react";
import type { AppConfig, Identity, ProfilePreferences, UserProfile } from "../types";
import { defaultProfilePreferences, profileInterests } from "../profile";
import { avatarStyles, eyebrowStyles, fieldLabelStyles, tripsPageStyles } from "../ui-styles";
import { ProfileAvatar } from "./ProfileAvatar";

const panel = "rounded-[22px] border border-[#e4e8f1] bg-white p-5 mobile:p-4";

export function Profile({ user, profile, config, onChange, onLeave, error }: {
  user: Identity["user"]; profile: UserProfile; config: AppConfig;
  onChange: (preferences: ProfilePreferences) => void;
  onLeave: () => Promise<void>; error: string;
}) {
  const values = { ...defaultProfilePreferences(config), ...profile.preferences };
  if (!config.origins.includes(values.origin)) values.origin = defaultProfilePreferences(config).origin;
  const update = (patch: Partial<ProfilePreferences>) => onChange({ ...values, ...patch });
  useEffect(() => () => { void onLeave(); }, [onLeave]);
  return <div data-ui="profile-page" className={tripsPageStyles}>
    <span className={eyebrowStyles}>ВАШЕ МЕСТО В «РЯДОМ»</span>
    <h1 className="mb-3">Профиль</h1>
    <p className="text-muted text-[14px] leading-[1.7] mb-4">Немного о вас — чтобы каждая поездка была ближе.</p>
    <div className="grid gap-4">
      <div className={`${panel} flex items-center gap-4`}>
        <span data-ui="profile-preview avatar" className={`${avatarStyles} !size-18 !text-[24px] shrink-0`}>
          <ProfileAvatar user={user} />
        </span>
        <div className="min-w-0"><strong className="block text-[18px] break-words">{[user.first_name, user.last_name].filter(Boolean).join(" ")}</strong>
          <span className="text-muted text-[12px]">Ваш профиль путешественника</span></div>
      </div>
      <fieldset className={`${panel} min-w-0 grid gap-5`}>
        <legend className="sr-only">Предпочтения для поездок</legend>
        <div><h2 className="text-[17px] font-bold">Поездки по вашему вкусу</h2>
          <p className="text-muted text-[12px] leading-[1.7] mt-1">Настройки сохраняются автоматически и подставляются в анкету. Перед поездкой их можно изменить.</p></div>
        <label className={`${fieldLabelStyles} relative`}>Город отправления
          <select className="appearance-none !pr-9" name="origin" aria-label="Город отправления" value={values.origin} onChange={(e) => update({ origin: e.target.value })}>
            {config.origins.map((city) => <option key={city}>{city}</option>)}
          </select><ChevronDown size={18} aria-hidden="true" className="absolute right-3.5 bottom-[17px] pointer-events-none text-muted" /></label>
        <label className={`${fieldLabelStyles} relative`}>Темп поездок
          <select className="appearance-none !pr-9" name="pace" aria-label="Темп поездок" value={values.pace} onChange={(e) => update({ pace: e.target.value as ProfilePreferences['pace'] })}>
            <option value="relaxed">Без спешки</option><option value="balanced">Всего понемногу</option><option value="intensive">Больше впечатлений</option>
          </select><ChevronDown size={18} aria-hidden="true" className="absolute right-3.5 bottom-[17px] pointer-events-none text-muted" /></label>
        <label className="block text-[14px] font-bold">Насколько далеко предлагать города
          <span className="flex justify-between items-center mt-3 text-[13px] font-medium"><span>По прямой от города отправления</span><output className="text-brand whitespace-nowrap ml-2">До {values.max_distance_km} км</output></span>
          <input type="range" name="max_distance_km" aria-label="Дальность подбора городов" min={300} max={600} step={50}
            value={values.max_distance_km} onChange={(e) => update({ max_distance_km: Number(e.target.value) })}
            className="w-full accent-brand mt-1" />
          <span className="flex justify-between text-[12px] text-muted font-medium"><span>300 км</span><span>600 км</span></span>
        </label>
        <label className={`${fieldLabelStyles} relative`}>Предпочтительный транспорт
          <select className="appearance-none !pr-9" name="preferred_transport" aria-label="Предпочтительный транспорт"
            value={values.preferred_transport} onChange={(e) => update({ preferred_transport: e.target.value as ProfilePreferences['preferred_transport'] })}>
            <option value="bus">Автобус</option><option value="suburban">Электричка</option><option value="car">Автомобиль</option>
          </select><ChevronDown size={18} aria-hidden="true" className="absolute right-3.5 bottom-[17px] pointer-events-none text-muted" /></label>
        <div><h2 className="text-[14px] font-bold mb-3">Что вам интересно</h2>
          <div className="flex flex-wrap gap-2">{profileInterests.map((interest) => <button type="button" key={interest}
            aria-pressed={values.interests.includes(interest)} className={`px-3 py-2 rounded-xl border text-[12px] ${values.interests.includes(interest) ? 'bg-[#edf0ff] border-brand text-brand' : 'bg-white border-[#e4e8f1] text-muted'}`}
            onClick={() => update({ interests: values.interests.includes(interest) ? values.interests.filter((value) => value !== interest) : [...values.interests, interest] })}>{interest}</button>)}</div>
        </div>
      </fieldset>
      {error && <p role="alert" className="text-red-700 text-[13px]">{error}</p>}
    </div>
  </div>;
}
