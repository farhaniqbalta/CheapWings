/** Display names for flight sources, shared by the search form and status views. */
export const SOURCE_NAMES: Record<string, string> = {
  skiplagged: "Skiplagged",
  swoop: "swoop (Google Flights)",
  octotrip: "OctoTrip",
  fli: "Fli (Google Flights)",
};

export const sourceName = (id: string) => SOURCE_NAMES[id] ?? id;
