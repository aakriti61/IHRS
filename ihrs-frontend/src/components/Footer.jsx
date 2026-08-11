import { useEffect, useState } from "react";
import api from "../api/axios.js";

export default function Footer() {
  const [contact, setContact] = useState(null);

  useEffect(() => {
    api.get("/auth/contact/").then((res) => setContact(res.data.data)).catch(() => {});
  }, []);

  return (
    <footer className="border-t border-ink/10 bg-surface">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal font-display text-xs font-semibold text-white">
            IH
          </span>
          <span className="font-display text-sm text-ink/70">
            IHRS — Interoperable Hospital Record Sharing
          </span>
        </div>
        {contact && (contact.address || contact.phone) && (
          <p className="text-xs text-ink/50">
            {contact.address}
            {contact.address && contact.phone && " · "}
            {contact.phone}
          </p>
        )}
      </div>
    </footer>
  );
}