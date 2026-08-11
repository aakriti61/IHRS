import { useState } from "react";

export default function PasswordField({ label, value, onChange, placeholder, required, minLength }) {
  const [visible, setVisible] = useState(false);

  return (
    <label className="block">
      <span className="text-sm font-medium text-ink/80">{label}</span>
      <div className="relative mt-1">
        <input
          required={required}
          minLength={minLength}
          type={visible ? "text" : "password"}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="w-full rounded-lg border border-ink/15 bg-white px-3.5 py-2.5 pr-10 text-sm text-ink placeholder:text-ink/35 focus:border-teal"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink/70"
          aria-label={visible ? "Hide password" : "Show password"}
        >
          {visible ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.1A9.4 9.4 0 0112 5c5 0 9 4 10.5 7-.6 1.2-1.5 2.5-2.7 3.6M6.5 6.5C4 8 2.3 10 1.5 12c1.5 3 5.5 7 10.5 7 1.4 0 2.7-.3 3.9-.8" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          )}
        </button>
      </div>
    </label>
  );
}