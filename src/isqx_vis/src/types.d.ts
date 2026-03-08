/** A unique, dot-separated public import path for a quantity kind. */
export type PublicApiPath = string;

/** A numeric index corresponding to a node's position in the `nodes` array. */
export type NodeIndex = number;

//
// raw data structures from objects.json
//

export type StrFragment = string | { text: string; path: PublicApiPath };

export interface TaggedNode<Tag extends string, Data> {
  tag: Tag;
  data: Data;
}

export type UnitDeclTag =
  | "base_unit"
  | "base_dimension"
  | "dimensionless"
  | "alias"
  | "translated"
  | "derived";

export type UnitScalar =
  | TaggedNode<"int", { text: string; value: number }>
  | TaggedNode<"float", { text: string; value: number }>
  | TaggedNode<"decimal", { text: string; value: string }>
  | TaggedNode<
      "fraction",
      { text: string; numerator: number; denominator: number }
    >
  | TaggedNode<"constant", { text: string; value: string }>
  | TaggedNode<"literal", { text: string; value: string }>;

export type UnitRef = {
  path: PublicApiPath;
  name: string;
};

export interface UnitFactorProduct {
  base: UnitScalar;
  exponent?: UnitScalar;
}

export type UnitFactor =
  | TaggedNode<"number", { value: UnitScalar }>
  | TaggedNode<"prefix", { name: string; value: UnitScalar }>
  | TaggedNode<"lazy_product", { products: UnitFactorProduct[] }>;

export interface UnitQuantity {
  value: UnitFactor;
  unit: UnitExpr;
}

export type UnitTag =
  | TaggedNode<
      "ratio_between",
      {
        numerator: UnitExpr;
        denominatorExpr?: UnitExpr;
        denominatorQuantity?: UnitQuantity;
      }
    >
  | TaggedNode<"origin_at", { quantity?: UnitQuantity; value?: string }>
  | TaggedNode<string, { text: string; value?: string; rank?: number }>;

export type UnitExpr =
  | TaggedNode<"ref", UnitRef>
  | TaggedNode<"pow", { base: UnitExpr; exponent: UnitScalar }>
  | TaggedNode<"mul", { terms: UnitExpr[] }>
  | TaggedNode<"scaled", { factor: UnitFactor; unit: UnitExpr }>
  | TaggedNode<"tagged", { unit: UnitExpr; tags: UnitTag[] }>
  | TaggedNode<"log", { base: UnitScalar; unit: UnitExpr }>;

export type UnitDecl =
  | TaggedNode<"base_unit", { path: PublicApiPath; name: string }>
  | TaggedNode<"base_dimension", { path: PublicApiPath; name: string }>
  | TaggedNode<"dimensionless", { path: PublicApiPath; name: string }>
  | TaggedNode<
      "alias",
      {
        path: PublicApiPath;
        name: string;
        expr: UnitExpr;
        allowPrefix?: boolean;
      }
    >
  | TaggedNode<
      "translated",
      { path: PublicApiPath; name: string; expr: UnitExpr; offset: UnitScalar }
    >
  | TaggedNode<"derived", { path: PublicApiPath; expr: UnitExpr }>;

/** A variable within the context of an equation. */
export interface WhereClause {
  symbol: string;
  description: StrFragment | StrFragment[];
  unit?: UnitExpr;
}

export interface KaTeXWhere {
  katex: string;
  where?: WhereClause[];
}

export interface SymbolDetail extends KaTeXWhere {
  remarks?: string;
}

export interface EquationDetail extends KaTeXWhere {
  assumptions?: (StrFragment | StrFragment[])[];
}

export interface WikidataDetail {
  qcode: string;
}

export interface QtyKindDetail {
  parent?: PublicApiPath;
  unit_si_coherent?: UnitExpr;
  tags?: string[];
  wikidata?: WikidataDetail[];
  symbols?: SymbolDetail[];
  equations?: EquationDetail[];
}

/** The root data structure loaded from the `objects.json` file. */
export type QtyKindData = Record<PublicApiPath, QtyKindDetail>;

export interface Quantity {
  value: string; // for now
  unit: UnitExpr | null;
}

export type ConstantsData = Record<PublicApiPath, Quantity>;

export type UnitsData = Record<PublicApiPath, UnitDecl>;

export interface IsqxData {
  qtyKinds: QtyKindData;
  constants: ConstantsData;
  units: UnitsData;
}

//
// processed graph and state structures
//

/**
 * A node in the graph after being processed for visualization.
 * It contains layout information from D3 and a reference to its original data.
 */
export interface GraphNode {
  publicApiPath: PublicApiPath;
  details: QtyKindDetail;
  x: number;
  y: number;
  radius: number;
  isGroup: boolean;
  value: number;
}

/**
 * A link between two nodes, using numeric indices.
 * This is the final link structure used by the application state.
 */
export interface GraphLink {
  source: NodeIndex;
  target: NodeIndex;
}

/** The main reactive state of the application. */
export interface AppState {
  data: QtyKindData | null;
  units: UnitsData;
  nodes: GraphNode[];
  links: GraphLink[];
  linkMap: Map<number, GraphLink[]>;
  colorMap: string[];
  ui: {
    /** The indices of all nodes the user has explicitly clicked to select. */
    selectedNodeIndices: NodeIndex[];
    /** The index of the node currently under the pointer (hovered), or null. */
    highlightedNodeIndex: NodeIndex | null;
    /** The current zoom and pan state of the SVG canvas. */
    view: { k: number; x: number; y: number };
  };
}
