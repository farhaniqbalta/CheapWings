/** Portable local lookup and resolution: no React, networking or provider code. */
export interface LocationEntity {
  id: string; type: "airport" | "city" | "country"; name: string;
  country: string; country_name: string; codes: string[]; aliases: string[];
  code?: string; city?: string; region?: string;
}
export interface LocationCatalog {
  version: string; definition: string; entities: LocationEntity[];
  major: Record<string, {codes: string[]; rationale: string}>;
}
export interface MajorSelection {
  type: "city" | "country"; location_id: string;
  coverage_mode: "major"; catalog_version: string;
}
export const fold = (s: string) => s.normalize("NFKD").toLowerCase().replace(/\p{M}/gu, "");
export function createLocationService(catalog: LocationCatalog) {
  const byId = new Map(catalog.entities.map(e => [e.id, e]));
  const airports = new Map(catalog.entities.filter(e => e.type === "airport").map(e => [e.code!, e]));
  const index = catalog.entities.map(entity => ({entity, text: fold([
    entity.name, entity.code ?? "", entity.city ?? "", entity.country_name, ...entity.aliases,
  ].join(" "))}));
  return {
    airport: (code: string) => airports.get(code),
    search(text: string, parentId?: string): LocationEntity[] {
      const term = fold(text.trim());
      const parent = parentId ? byId.get(parentId) : undefined;
      const allowed = parent ? new Set(parent.codes) : null;
      if (parentId && !parent) return [];
      if (!term && !allowed) return [];
      const rank = (e: LocationEntity) => term === fold(e.code ?? "") ? 0
        : term === fold(e.name) || e.aliases.some(a => term === fold(a)) ? 1 : 2;
      return index.filter(({entity:e, text:key}) => (!allowed || e.type === "airport" && allowed.has(e.code!))
        && (!term || key.includes(term)))
        .map(i => i.entity).sort((a,b) => rank(a)-rank(b) || a.type.localeCompare(b.type)
          || fold(a.name).localeCompare(fold(b.name)) || a.id.localeCompare(b.id));
    },
    resolve(id: string) {
      const entity = byId.get(id);
      const mapping = catalog.major[id];
      if (!entity || entity.type === "airport" || !mapping) return null;
      return {selection: {type: entity.type, location_id:id, coverage_mode:"major",
        catalog_version:catalog.version} as MajorSelection,
        codes: [...new Set(mapping.codes)].sort(), rationale:mapping.rationale};
    },
  };
}
export type LocationService = ReturnType<typeof createLocationService>;
