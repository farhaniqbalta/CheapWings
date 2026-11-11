import { useId, useState } from "react";
import type { LocationEntity, LocationService, MajorSelection } from "../lib/locations";

interface Props {
  label: string; codes: string[]; onChange: (codes: string[], selection?: MajorSelection | null) => void;
  locations: LocationService | null;
}

/** Parent locations navigate airport rows; only a physical airport commits a chip. */
export function AirportMultiSelect({ label, codes, onChange, locations }: Props) {
  const inputId = useId();
  const [mode, setMode] = useState<"specific" | "major">("specific");
  const [confirmSwitch, setConfirmSwitch] = useState(false);
  const [rationale, setRationale] = useState("");
  const [draft, setDraft] = useState("");
  const [parent, setParent] = useState<LocationEntity | null>(null);
  const [open, setOpen] = useState(false);
  const [navigating, setNavigating] = useState(false);
  const [active, setActive] = useState(0);
  const [visible, setVisible] = useState(30);
  const [message, setMessage] = useState("");
  const matches = (locations?.search(draft, mode === "specific" ? parent?.id : undefined) ?? []).filter(e => mode === "specific" || e.type !== "airport");
  const rows = matches.slice(0, visible);
  const select = (entity: LocationEntity) => {
    setActive(0); setVisible(30); setDraft(""); setOpen(true);
    if (mode === "major") {
      const resolved = locations?.resolve(entity.id);
      setParent(entity);
      if (!resolved) {
        onChange([], null); setRationale("");
        setMessage(`No curated major-airport mapping for ${entity.name}. Use Specific Airports to choose manually.`);
      } else {
        onChange(resolved.codes, resolved.selection); setRationale(resolved.rationale);
        setMessage(`${entity.name}: ${resolved.codes.length} major airports selected. Review the complete list before searching.`);
      }
      setOpen(false);
    } else if (entity.type === "airport") {
      if (!codes.includes(entity.code!)) onChange([...codes, entity.code!]);
      setMessage(`${entity.code} selected. ${codes.includes(entity.code!) ? codes.length : codes.length+1} airports.`);
    } else {
      setParent(entity);
      setMessage(`Browsing ${entity.name}. Choose exact airports; none added automatically.`);
    }
  };
  return <div className="field location-picker">
    <label htmlFor={inputId}>{label}</label>
    <div className="location-mode" role="group" aria-label={`${label} coverage mode`}>
      <button type="button" aria-pressed={mode === "specific"} onClick={() => {
        setMode("specific"); setConfirmSwitch(false); setParent(null); setDraft("");
        setOpen(false); onChange(codes, null);
        setMessage("Specific Airports: retained the displayed airports. Remove chips to narrow your scope.");
      }}>Specific Airports</button>
      <button type="button" aria-pressed={mode === "major"} onClick={() => {
        if (mode === "major") return;
        if (codes.length) {setConfirmSwitch(true); return;}
        setMode("major"); setParent(null); setDraft(""); setOpen(false);
        setMessage("Choose one city or country for curated major coverage.");
      }}>Major Airports</button>
    </div>
    {confirmSwitch && <div className="location-major">
      <p>To choose a Major location, first clear these {codes.length} airport selections.</p>
      <button type="button" onClick={() => {
        onChange([], null); setMode("major"); setConfirmSwitch(false); setParent(null);
        setDraft("");setOpen(false);setRationale("");setMessage("Choose one city or country.");
      }}>Clear airports and choose Major</button>
      <button type="button" onClick={() => setConfirmSwitch(false)}>Keep Specific Airports</button>
    </div>}
    <p className="location-hint">{mode === "specific" ? "Search an airport, city or country; choose exact airports." : "Select one city or country. A new location replaces the previous Major selection."}</p>
    <div className="chip-input">
      {codes.map(code => <span className="chip" key={code} title={locations?.airport(code)?.name}>
        {code}{mode === "specific" && <button type="button" aria-label={`Remove ${code}`} onClick={() => {
          onChange(codes.filter(c => c !== code)); setMessage(`${code} removed.`);
        }}>×</button>}
      </span>)}
      <input id={inputId} role="combobox" aria-autocomplete="list" aria-expanded={open}
        aria-controls={open ? `${inputId}-list` : undefined} aria-activedescendant={open && rows[active] ? `${inputId}-option-${active}` : undefined}
        aria-describedby={`${inputId}-help`} autoComplete="off" maxLength={100}
        value={draft} placeholder={mode === "specific" ? "Airport, city or country" : "City or country for major airports"} disabled={!locations}
        onFocus={() => setOpen(true)}
        onBlur={event => {if (!event.currentTarget.closest('.location-picker')?.contains(event.relatedTarget)) setOpen(false);}}
        onChange={event => {setDraft(event.target.value); setNavigating(false); setOpen(true); setActive(0); setVisible(30);}}
        onKeyDown={event => {
          if (event.key === "Escape") {event.preventDefault(); setOpen(false);}
          if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault(); setOpen(true); setNavigating(true);
            const next = Math.max(0, Math.min(rows.length-1, active+(event.key === "ArrowDown" ? 1 : -1)));
            setActive(next);
            document.getElementById(`${inputId}-option-${next}`)?.scrollIntoView({block:"nearest"});
          }
          if (event.key === "Enter" || event.key === " " && navigating && open && rows[active]) {
            event.preventDefault();
            if (open && rows[active]) select(rows[active]);
            else setMessage("No matching location. Choose an airport from the catalog.");
          }
        }} />
    </div>
    {mode === "specific" && parent && <div className="location-context">Browsing {parent.name} · {parent.country_name}
      <button type="button" onClick={() => {setParent(null);setDraft("");setActive(0);setOpen(true);}}>Clear location filter</button>
    </div>}
    {mode === "major" && <div className="location-major">
      <strong>Major airports only — not all airports in this location</strong>
      {parent && <p>{parent.name} · {parent.country_name} · {codes.length} airports included</p>}
      {rationale && <p>{rationale}</p>}
      <p>Switch to Specific Airports to retain and manually narrow the displayed airports.</p>
    </div>}
    {open && <div className="location-results">
      <p role="status" className="location-hint">{matches.length} suggestions · {rows.length} shown. Use arrows and Enter to select.</p>
      <div role="listbox" id={`${inputId}-list`} aria-label={`${label} suggestions`} aria-multiselectable="true">
        {rows.map((entity, i) => <div key={entity.id} role="option" id={`${inputId}-option-${i}`}
          aria-selected={entity.type === "airport" && codes.includes(entity.code!)}
          className={active === i ? "location-row active" : "location-row"}
          onMouseDown={e => e.preventDefault()} onClick={() => select(entity)}>
          <strong>{entity.code ?? entity.name}</strong>
          <span>{entity.type === "airport" ? entity.name : `${entity.type === "city" ? "City" : "Country"} · ${mode === "specific" ? "Browse airports" : "Major coverage"}`}</span>
          <small>{[entity.city, entity.region, entity.country_name].filter(Boolean).join(", ")}</small>
          <small>{entity.type === "airport" ? "Airport" : entity.type === "city" ? "City" : "Country"}</small>
        </div>)}
      </div>
      {!matches.length && <p>{draft ? "No matching location. Try a code, name or alias." : "Type to find locations."}</p>}
      {matches.length > rows.length && <button type="button" onClick={() => setVisible(n => n+30)}>Show more ({rows.length} of {matches.length} results)</button>}
    </div>}
    <p id={`${inputId}-help`} className="location-hint" role="status" aria-live="polite">{message || `${codes.length} airports selected. Typing does not start a flight search.`}</p>
    {!!codes.length && <ul className="location-selection" aria-label={`${label} selected airports`}>{codes.map(code =>
      <li key={code}>{code} · {locations?.airport(code)?.name ?? code}</li>)}</ul>}
  </div>;
}
