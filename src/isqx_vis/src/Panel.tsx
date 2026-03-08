import type { Component, ParentComponent } from "solid-js";
import { createStore } from "solid-js/store";
import { For, Match, Show, Switch, createMemo, lazy } from "solid-js";
import type {
  AppState,
  GraphNode,
  StrFragment,
  SymbolDetail,
  EquationDetail,
  WikidataDetail,
  PublicApiPath,
  UnitsData,
  UnitExpr,
  UnitFactor,
  UnitRef,
  UnitScalar,
  UnitTag,
  UnitQuantity
} from "./types";
import { niceName, findPublicApiPathInDescription } from "./utils";
import styles from "./Panel.module.scss";
import { useJumper } from "./JumpContext";

const KaTeX = lazy(() => import("./KaTeX"));

const CrossRef: ParentComponent<{
  targetPath: PublicApiPath;
}> = props => {
  const jumpToNode = useJumper();
  const handleClick = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    jumpToNode!(props.targetPath);
  };

  return (
    <a href="#" onClick={handleClick}>
      {props.children}
    </a>
  );
};

function isAnchor(
  fragment: StrFragment
): fragment is { text: string; path: string } {
  return (
    typeof fragment === "object" && fragment !== null && "path" in fragment
  );
}

const RenderFragment: Component<{
  fragment: StrFragment;
  noLinks?: boolean;
}> = props => {
  const fragment = () => props.fragment;

  return (
    <Show
      when={isAnchor(fragment()) && !props.noLinks}
      fallback={
        <>
          {isAnchor(fragment())
            ? (fragment() as { text: string }).text
            : fragment()}
        </>
      }
    >
      <CrossRef targetPath={(fragment() as { path: string }).path}>
        {(fragment() as { text: string }).text}
      </CrossRef>
    </Show>
  );
};

const RenderFragments: Component<{
  fragments: StrFragment | StrFragment[];
  noLinks?: boolean;
}> = props => {
  const fragments = () =>
    Array.isArray(props.fragments) ? props.fragments : [props.fragments];
  return (
    <For each={fragments()}>
      {fragment => (
        <RenderFragment fragment={fragment} noLinks={props.noLinks} />
      )}
    </For>
  );
};

const unitPrecedence = (variant: string): number => {
  switch (variant) {
    case "mul":
      return 1;
    case "scaled":
      return 2;
    case "log":
      return 3;
    case "tagged":
      return 4;
    case "pow":
      return 5;
    default:
      return 6;
  }
};

const RenderUnitScalar: Component<{ scalar: UnitScalar }> = props => {
  return <>{props.scalar.data.text}</>;
};

const getUnitDisplayName = (unit: UnitRef): string => unit.name;

const RenderUnitRef: Component<{
  unit: UnitRef;
  noLinks?: boolean;
}> = props => {
  const displayName = () => getUnitDisplayName(props.unit);

  return (
    <Show when={!props.noLinks} fallback={<span>{displayName()}</span>}>
      <CrossRef targetPath={props.unit.path}>{displayName()}</CrossRef>
    </Show>
  );
};

function isRatioTag(
  tag: UnitTag
): tag is Extract<UnitTag, { tag: "ratio_between" }> {
  return tag.tag === "ratio_between";
}

function isOriginTag(
  tag: UnitTag
): tag is Extract<UnitTag, { tag: "origin_at" }> {
  return tag.tag === "origin_at";
}

function isConstantScalar(
  scalar: UnitScalar
): scalar is Extract<UnitScalar, { tag: "constant" }> {
  return scalar.tag === "constant";
}

const RenderUnitFactor: Component<{ factor: UnitFactor }> = props => {
  const numberValue = () =>
    props.factor.tag === "number" ? props.factor.data.value : undefined;
  const prefixData = () =>
    props.factor.tag === "prefix" ? props.factor.data : undefined;
  const lazyProducts = () =>
    props.factor.tag === "lazy_product" ? props.factor.data.products : [];

  return (
    <Switch fallback={<RenderUnitScalar scalar={numberValue()!} />}>
      <Match when={props.factor.tag === "prefix"}>{prefixData()!.name}</Match>
      <Match when={props.factor.tag === "lazy_product"}>
        <For each={lazyProducts()}>
          {(product, i) => (
            <>
              <RenderUnitScalar scalar={product.base} />
              <Show when={product.exponent}>
                <sup>
                  <RenderUnitScalar scalar={product.exponent!} />
                </sup>
              </Show>
              {i() < lazyProducts().length - 1 ? " · " : ""}
            </>
          )}
        </For>
      </Match>
    </Switch>
  );
};

const RenderUnitQuantity: Component<{
  quantity: UnitQuantity;
  units: UnitsData;
  noLinks?: boolean;
}> = props => (
  <>
    <RenderUnitFactor factor={props.quantity.value} />{" "}
    <RenderUnit
      unit={props.quantity.unit}
      units={props.units}
      noLinks={props.noLinks}
    />
  </>
);

const RenderUnitTag: Component<{
  tag: UnitTag;
  units: UnitsData;
  noLinks?: boolean;
}> = props => {
  const literalData = () =>
    !isRatioTag(props.tag) && !isOriginTag(props.tag)
      ? props.tag.data
      : undefined;
  const ratioData = () => (isRatioTag(props.tag) ? props.tag.data : undefined);
  const originData = () =>
    isOriginTag(props.tag) ? props.tag.data : undefined;

  return (
    <Switch fallback={<>{literalData()!.text}</>}>
      <Match when={props.tag.tag === "ratio_between"}>
        <>
          <code>
            <RenderUnit
              unit={ratioData()!.numerator}
              units={props.units}
              noLinks={props.noLinks}
            />
          </code>
          {" to "}
          <code>
            <Show
              when={ratioData()!.denominatorQuantity}
              fallback={
                <RenderUnit
                  unit={ratioData()!.denominatorExpr!}
                  units={props.units}
                  noLinks={props.noLinks}
                />
              }
            >
              <RenderUnitQuantity
                quantity={ratioData()!.denominatorQuantity!}
                units={props.units}
                noLinks={props.noLinks}
              />
            </Show>
          </code>
        </>
      </Match>
      <Match when={props.tag.tag === "origin_at"}>
        <>
          {"relative to "}
          <code>
            <Show
              when={originData()!.quantity}
              fallback={<>{originData()!.value}</>}
            >
              <RenderUnitQuantity
                quantity={originData()!.quantity!}
                units={props.units}
                noLinks={props.noLinks}
              />
            </Show>
          </code>
        </>
      </Match>
    </Switch>
  );
};

const RenderUnit: Component<{
  unit: UnitExpr;
  units: UnitsData;
  noLinks?: boolean;
  parentPrecedence?: number;
}> = props => {
  const variant = props.unit.tag;
  const precedence = unitPrecedence(variant);
  const needsParens = () => (props.parentPrecedence ?? 0) >= precedence;
  const refData = () =>
    props.unit.tag === "ref" ? props.unit.data : undefined;
  const powData = () =>
    props.unit.tag === "pow" ? props.unit.data : undefined;
  const mulData = () =>
    props.unit.tag === "mul" ? props.unit.data : undefined;
  const scaledData = () =>
    props.unit.tag === "scaled" ? props.unit.data : undefined;
  const taggedData = () =>
    props.unit.tag === "tagged" ? props.unit.data : undefined;
  const logData = () =>
    props.unit.tag === "log" ? props.unit.data : undefined;

  return (
    <>
      {needsParens() ? "(" : ""}
      <Switch
        fallback={<RenderUnitRef unit={refData()!} noLinks={props.noLinks} />}
      >
        <Match when={variant === "pow"}>
          <>
            <RenderUnit
              unit={powData()!.base}
              units={props.units}
              noLinks={props.noLinks}
              parentPrecedence={precedence}
            />
            <sup>
              <RenderUnitScalar scalar={powData()!.exponent} />
            </sup>
          </>
        </Match>
        <Match when={variant === "mul"}>
          <For each={mulData()?.terms ?? []}>
            {(term, i) => (
              <>
                <RenderUnit
                  unit={term}
                  units={props.units}
                  noLinks={props.noLinks}
                  parentPrecedence={precedence}
                />
                {i() < (mulData()?.terms.length ?? 0) - 1 ? " · " : ""}
              </>
            )}
          </For>
        </Match>
        <Match when={variant === "scaled"}>
          <>
            <RenderUnitFactor factor={scaledData()!.factor} />
            {" · "}
            <RenderUnit
              unit={scaledData()!.unit}
              units={props.units}
              noLinks={props.noLinks}
              parentPrecedence={precedence}
            />
          </>
        </Match>
        <Match when={variant === "tagged"}>
          <>
            <RenderUnit
              unit={taggedData()!.unit}
              units={props.units}
              noLinks={props.noLinks}
              parentPrecedence={precedence}
            />
            {"["}
            <For each={taggedData()?.tags ?? []}>
              {(tag, i) => (
                <>
                  <RenderUnitTag
                    tag={tag}
                    units={props.units}
                    noLinks={props.noLinks}
                  />
                  {i() < (taggedData()?.tags.length ?? 0) - 1 ? ", " : ""}
                </>
              )}
            </For>
            {"]"}
          </>
        </Match>
        <Match when={variant === "log"}>
          {(() => {
            const log = logData()!;
            const base = log.base;

            return (
              <>
                {isConstantScalar(base) && base.data.value === "E" ? (
                  "ln"
                ) : (
                  <>
                    <span>log</span>
                    <sub>
                      <RenderUnitScalar scalar={base} />
                    </sub>
                  </>
                )}
                {"("}
                <RenderUnit
                  unit={log.unit}
                  units={props.units}
                  noLinks={props.noLinks}
                  parentPrecedence={precedence}
                />
                {")"}
              </>
            );
          })()}
        </Match>
      </Switch>
      {needsParens() ? ")" : ""}
    </>
  );
};

const Symbol: Component<{ symbol: SymbolDetail }> = props => (
  <>
    <KaTeX text={props.symbol.katex} />
    <Show when={props.symbol.remarks}>
      <span class={styles.symbolRemarks}> ({props.symbol.remarks})</span>
    </Show>
  </>
);

const EquationsSection: Component<{
  equations: EquationDetail[] | undefined;
  units: UnitsData;
}> = props => (
  <Show when={props.equations && props.equations.length > 0}>
    <div class={styles.detailSection}>
      <h4 style={{ color: "var(--accent-green)" }}>Equations</h4>
      <For each={props.equations}>
        {eq => (
          <div class={styles.equationBlock}>
            <KaTeX text={eq.katex} display={true} />
            <Show when={eq.where}>
              <div class={styles.whereClause}>
                <For each={eq.where}>
                  {w => (
                    <div class={styles.whereRow}>
                      <span class={styles.whereSymbol}>
                        <KaTeX text={w.symbol} />
                      </span>
                      <span>=</span>
                      <span>
                        <RenderFragments fragments={w.description} />
                        <Show when={w.unit}>
                          <>
                            {" ("}
                            <RenderUnit
                              unit={w.unit!}
                              units={props.units}
                              noLinks
                            />
                            {")"}
                          </>
                        </Show>
                      </span>
                    </div>
                  )}
                </For>
              </div>
            </Show>
          </div>
        )}
      </For>
    </div>
  </Show>
);

const IncomingLinksSection: Component<{
  node: GraphNode;
  index: number;
  store: AppState;
}> = props => {
  const hydratedLinks = createMemo(() => {
    const links = props.store.linkMap.get(props.index) ?? [];
    return links
      .map(link => {
        if (link.source === props.index) return null; // only incoming
        const sourceNode = props.store.nodes[link.source];
        if (!sourceNode) return null;

        const relevantEquations =
          sourceNode.details.equations?.filter(eq =>
            eq.where?.some(
              clause =>
                findPublicApiPathInDescription(clause.description) ===
                props.node.publicApiPath
            )
          ) ?? [];

        return {
          sourceNode,
          sourceIndex: link.source,
          equations: relevantEquations
        };
      })
      .filter(Boolean) as {
      sourceNode: GraphNode;
      sourceIndex: number;
      equations: EquationDetail[];
    }[];
  });

  return (
    <Show when={hydratedLinks().length > 0}>
      <div class={styles.detailSection}>
        <h4 style={{ color: "var(--accent-blue)" }}>Referenced by</h4>
        <div class={styles.definedIn}>
          <For each={hydratedLinks()}>
            {({ sourceNode, sourceIndex, equations }) => (
              <div
                class={styles.definedInDetail}
                style={{
                  "border-left-color": props.store.colorMap[sourceIndex]
                }}
              >
                <CrossRef targetPath={sourceNode.publicApiPath}>
                  {niceName(sourceNode.publicApiPath)}
                </CrossRef>
                <For each={equations}>
                  {eq => (
                    <div class={styles.equationBlock}>
                      <KaTeX text={eq.katex} display={true} />
                    </div>
                  )}
                </For>
              </div>
            )}
          </For>
        </div>
      </div>
    </Show>
  );
};

const WikidataSection: Component<{
  wikidata: WikidataDetail[] | undefined;
}> = props => (
  <Show when={props.wikidata && props.wikidata.length > 0}>
    <div class={styles.detailSection}>
      <h4>Wikidata</h4>
      <For each={props.wikidata}>
        {(wd, i) => (
          <>
            <a
              href={`https://www.wikidata.org/wiki/${wd.qcode}`}
              target="_blank"
              rel="noopener"
            >
              {wd.qcode}
            </a>
            {i() < props.wikidata!.length - 1 ? " " : ""}
          </>
        )}
      </For>
    </div>
  </Show>
);

const NodeDetail: Component<{
  node: GraphNode;
  index: number;
  store: AppState;
  isExpanded: boolean;
  onToggle: () => void;
}> = props => {
  const details = () => props.node.details;
  const color = () => props.store.colorMap[props.index];

  return (
    <div class={styles.nodeDetail} style={{ "border-left-color": color() }}>
      <div class={styles.nodeHeader}>
        <h3 onClick={props.onToggle}>{niceName(props.node.publicApiPath)}</h3>
        <div class={styles.symbols}>
          <For each={details().symbols}>
            {(symbol, i) => (
              <>
                <Symbol symbol={symbol} />
                {i() < details().symbols!.length - 1 ? ", " : ""}
              </>
            )}
          </For>
        </div>
      </div>
      <div class={styles.publicApiPath}>{props.node.publicApiPath}</div>
      <Show when={props.isExpanded}>
        <EquationsSection
          equations={details().equations}
          units={props.store.units}
        />
        <IncomingLinksSection
          node={props.node}
          index={props.index}
          store={props.store}
        />
        <WikidataSection wikidata={details().wikidata} />
      </Show>
    </div>
  );
};

const Panel: Component<{
  store: AppState;
  onClearData: () => void;
}> = props => {
  const [expandedState, setExpandedState] = createStore<{
    [key: number]: boolean;
  }>({});

  const nodesToDisplay = createMemo(() => {
    const selected = props.store.ui.selectedNodeIndices;
    const highlighted = props.store.ui.highlightedNodeIndex;
    const allNodes = props.store.nodes;

    const orderedIndices = [...selected];
    if (highlighted !== null && !selected.includes(highlighted)) {
      orderedIndices.push(highlighted);
    }

    return orderedIndices.map(index => ({
      node: allNodes[index],
      index
    }));
  });

  const handleToggle = (index: number) => {
    const isCurrentlyExpanded = expandedState[index] ?? true;
    setExpandedState(index, !isCurrentlyExpanded);
  };

  const collapseAll = () => {
    const update: { [key: number]: boolean } = {};
    for (const { index } of nodesToDisplay()) {
      update[index] = false;
    }
    setExpandedState(update);
  };

  const showAll = () => {
    const update: { [key: number]: boolean } = {};
    for (const { index } of nodesToDisplay()) {
      update[index] = true;
    }
    setExpandedState(update);
  };

  const isExpanded = (index: number) => expandedState[index] ?? true;

  return (
    <>
      <div class={styles.controls}>
        <button onClick={props.onClearData}>Clear Data</button>
        <Show when={nodesToDisplay().length > 0}>
          <button onClick={collapseAll}>Collapse All</button>
          <button onClick={showAll}>Show All</button>
        </Show>
      </div>
      <div class={styles.nodeDetails}>
        <For each={nodesToDisplay()}>
          {({ node, index }) => (
            <>
              <Show
                when={
                  index === props.store.ui.highlightedNodeIndex &&
                  props.store.ui.selectedNodeIndices.length > 0 &&
                  !props.store.ui.selectedNodeIndices.includes(index)
                }
              >
                <hr class={styles.separator} />
              </Show>
              <NodeDetail
                node={node}
                index={index}
                store={props.store}
                isExpanded={isExpanded(index)}
                onToggle={() => handleToggle(index)}
              />
            </>
          )}
        </For>
      </div>
    </>
  );
};

export default Panel;
