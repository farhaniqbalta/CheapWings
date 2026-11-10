import type { SortMode } from "../api/types";

export function ResultSortBar({ sort, onChange }: { sort: SortMode; onChange: (s: SortMode) => void }) {
  return (
    <div className="sort-bar" role="group" aria-label="Sort results">
      <button
        type="button"
        className={sort === "best_checked" ? "sort-button active" : "sort-button"}
        aria-pressed={sort === "best_checked"}
        onClick={() => onChange("best_checked")}
      >
        Best checked deal
      </button>
      <button
        type="button"
        className={sort === "lowest_advertised" ? "sort-button active" : "sort-button"}
        aria-pressed={sort === "lowest_advertised"}
        onClick={() => onChange("lowest_advertised")}
      >
        Lowest advertised
      </button>
      {sort === "lowest_advertised" && (
        <span className="sort-caveat">Advertised prices may be estimates. Fees, restrictions and final availability must be checked with the seller.</span>
      )}
    </div>
  );
}
