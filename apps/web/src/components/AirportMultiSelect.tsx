import { useId, useState } from "react";

const IATA_RE = /^[A-Za-z]{3}$/;

interface Props {
  label: string;
  codes: string[];
  onChange: (codes: string[]) => void;
}

/** Free-text IATA code entry with removable chips. No airport name lookup is invented client-side. */
export function AirportMultiSelect({ label, codes, onChange }: Props) {
  const [draft, setDraft] = useState("");
  const [invalid, setInvalid] = useState<string | null>(null);
  const inputId = useId();

  const commit = () => {
    const candidate = draft.trim().toUpperCase();
    if (!candidate) return;
    if (!IATA_RE.test(candidate)) {
      setInvalid(`"${candidate}" is not a 3-letter airport code`);
      return;
    }
    if (!codes.includes(candidate)) onChange([...codes, candidate]);
    setDraft("");
    setInvalid(null);
  };

  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      <div className="chip-input">
        {codes.map((code) => (
          <span className="chip" key={code}>
            {code}
            <button
              type="button"
              aria-label={`Remove ${code}`}
              onClick={() => onChange(codes.filter((c) => c !== code))}
            >
              &times;
            </button>
          </span>
        ))}
        <input
          id={inputId}
          type="text"
          value={draft}
          placeholder={codes.length === 0 ? "e.g. MEL" : "Add another"}
          aria-describedby={invalid ? `${inputId}-error` : undefined}
          onChange={(e) => {
            setDraft(e.target.value);
            setInvalid(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              commit();
            } else if (e.key === "Backspace" && draft === "" && codes.length > 0) {
              onChange(codes.slice(0, -1));
            }
          }}
          onBlur={commit}
        />
      </div>
      {invalid && (
        <p role="alert" id={`${inputId}-error`} className="field-error">
          {invalid}
        </p>
      )}
    </div>
  );
}
