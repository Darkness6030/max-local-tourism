import { useState } from "react";
import { Compass } from "lucide-react";
import type { Identity } from "../types";

export function ProfileAvatar({ user }: { user?: Identity["user"] }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const photo = user?.photo_url;
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
      {[user.first_name, user.last_name]
        .filter(Boolean)
        .map((value) => value!.slice(0, 1))
        .join("")}
    </>
  ) : (
    <Compass size={20} />
  );
}
