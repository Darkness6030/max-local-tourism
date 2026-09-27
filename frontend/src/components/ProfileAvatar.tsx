import { useState } from "react";
import { Compass, Mountain, Sun } from "lucide-react";
import type { Identity, ProfilePreferences } from "../types";

export function ProfileAvatar({ user, preferences }: { user?: Identity["user"]; preferences?: ProfilePreferences }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const style = preferences?.avatar_style ?? "max";
  const Icon = style === "compass" ? Compass : style === "mountain" ? Mountain : style === "sun" ? Sun : null;
  if (Icon) return <Icon size={24} aria-hidden="true" />;
  const photo = style === "max" ? user?.photo_url : null;
  if (photo?.startsWith("https://") && photo !== failedUrl) {
    return (
      <img
        src={photo}
        alt=""
        referrerPolicy="no-referrer"
        onError={() => setFailedUrl(photo)}
      />
    );
  }
  return user ? (
    <>
      {(preferences?.display_name ? preferences.display_name.split(/\s+/).slice(0, 2) : [user.first_name, user.last_name])
        .filter(Boolean)
        .map((value) => value!.slice(0, 1))
        .join("")}
    </>
  ) : (
    <Compass size={20} />
  );
}
