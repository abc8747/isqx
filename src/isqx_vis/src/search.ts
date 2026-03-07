import type { CanonicalPath, GraphNode } from "./types";
import { niceName } from "./utils";

export type SearchEntry = {
  canonicalPath: CanonicalPath;
  index: number;
  name: string;
  normalizedName: string;
  normalizedPath: string;
};

export type SearchResult = SearchEntry & {
  score: number;
};

export const buildSearchEntries = (nodes: GraphNode[]): SearchEntry[] => {
  return nodes.map((node, index) => {
    const name = niceName(node.canonicalPath);
    return {
      canonicalPath: node.canonicalPath,
      index,
      name,
      normalizedName: normalizeSearchText(name),
      normalizedPath: normalizeSearchText(node.canonicalPath)
    };
  });
};

export const searchEntries = (
  entries: SearchEntry[],
  query: string,
  limit: number
) => {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) return [];

  const queryTokens = normalizedQuery.split(" ").filter(Boolean);

  return entries
    .map(entry => {
      const score = scoreSearchEntry(entry, normalizedQuery, queryTokens);
      return score === null ? null : { ...entry, score };
    })
    .filter((entry): entry is SearchResult => entry !== null)
    .sort((a, b) => {
      if (a.score !== b.score) return b.score - a.score;
      if (a.name.length !== b.name.length) return a.name.length - b.name.length;
      return a.index - b.index;
    })
    .slice(0, limit);
};

const normalizeSearchText = (text: string) => {
  return text
    .toLowerCase()
    .replace(/[._/]+/g, " ")
    .replace(/[^a-z0-9\s]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
};

const scoreSearchEntry = (
  entry: SearchEntry,
  normalizedQuery: string,
  queryTokens: string[]
) => {
  const exactName = entry.normalizedName === normalizedQuery;
  const exactPath = entry.normalizedPath === normalizedQuery;
  if (exactName) return 1200;
  if (exactPath) return 1150;

  const nameStartsWith = entry.normalizedName.startsWith(normalizedQuery);
  const pathStartsWith = entry.normalizedPath.startsWith(normalizedQuery);
  const nameIncludes = entry.normalizedName.includes(normalizedQuery);
  const pathIncludes = entry.normalizedPath.includes(normalizedQuery);

  const tokenCoverage = queryTokens.every(
    token =>
      entry.normalizedName.includes(token) || entry.normalizedPath.includes(token)
  );

  if (
    !nameStartsWith &&
    !pathStartsWith &&
    !nameIncludes &&
    !pathIncludes &&
    !tokenCoverage
  ) {
    return null;
  }

  let score = 0;

  if (nameStartsWith) score += 900;
  else if (nameIncludes) score += 700;

  if (pathStartsWith) score += 840;
  else if (pathIncludes) score += 640;

  if (tokenCoverage) {
    score += 80 + queryTokens.length * 25;
  }

  if (nameIncludes) {
    score -= entry.normalizedName.indexOf(normalizedQuery);
  }

  if (pathIncludes) {
    score -= entry.normalizedPath.indexOf(normalizedQuery);
  }

  return score;
};