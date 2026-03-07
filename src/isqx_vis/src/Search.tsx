import type { Component } from "solid-js";
import {
    For,
    Show,
    onCleanup,
    createEffect,
    createMemo,
    createSignal,
    onMount
} from "solid-js";
import type { CanonicalPath, GraphNode } from "./types";
import { buildSearchEntries, searchEntries } from "./search";
import styles from "./Search.module.scss";

const MAX_RESULTS = 10;

const Search: Component<{
    onAddToSelection?: (path: CanonicalPath) => void;
    nodes: GraphNode[];
    onSelect: (path: CanonicalPath) => void;
    onPreview?: (path: CanonicalPath | null) => void;
    setApi?: (api: { focus: () => void }) => void;
    shortcutHint?: string;
}> = props => {
    const [query, setQuery] = createSignal("");
    const [isOpen, setIsOpen] = createSignal(false);
    const [activeIndex, setActiveIndex] = createSignal(0);
    const [hoveredIndex, setHoveredIndex] = createSignal<number | null>(null);
    let inputRef: HTMLInputElement | undefined;
    let previewTimeoutId: number | undefined;

    const entries = createMemo(() => buildSearchEntries(props.nodes));
    const results = createMemo(() =>
        searchEntries(entries(), query(), MAX_RESULTS)
    );

    createEffect(() => {
        query();
        setActiveIndex(0);
        setHoveredIndex(null);
    });

    onMount(() => {
        props.setApi?.({
            focus: () => {
                inputRef?.focus();
                inputRef?.select();
                setIsOpen(query().trim().length > 0);
            }
        });
    });

    onCleanup(() => {
        cancelPreviewTimeout();
        props.onPreview?.(null);
    });

    const cancelPreviewTimeout = () => {
        if (previewTimeoutId === undefined) return;
        window.clearTimeout(previewTimeoutId);
        previewTimeoutId = undefined;
    };

    const schedulePreview = (path: CanonicalPath | null) => {
        cancelPreviewTimeout();
        previewTimeoutId = window.setTimeout(() => {
            props.onPreview?.(path);
            previewTimeoutId = undefined;
        }, 140);
    };

    const activeResultIndex = () => hoveredIndex() ?? activeIndex();

    const commitSelection = (path: CanonicalPath) => {
        cancelPreviewTimeout();
        props.onPreview?.(null);
        props.onSelect(path);
        setQuery("");
        setIsOpen(false);
        setActiveIndex(0);
        setHoveredIndex(null);
        inputRef?.blur();
    };

    const addToSelection = (path: CanonicalPath) => {
        cancelPreviewTimeout();
        props.onPreview?.(null);
        props.onAddToSelection?.(path);
        inputRef?.focus();
    };

    const handleKeyDown = (event: KeyboardEvent) => {
        const currentResults = results();

        if (event.key === "ArrowDown") {
            if (currentResults.length === 0) return;
            event.preventDefault();
            setIsOpen(true);
            setActiveIndex(index => Math.min(index + 1, currentResults.length - 1));
            return;
        }

        if (event.key === "ArrowUp") {
            if (currentResults.length === 0) return;
            event.preventDefault();
            setIsOpen(true);
            setActiveIndex(index => Math.max(index - 1, 0));
            return;
        }

        if (event.key === "Enter") {
            if (currentResults.length === 0) return;
            event.preventDefault();
            const result = currentResults[activeResultIndex()] ?? currentResults[0];
            if (result) commitSelection(result.canonicalPath);
            return;
        }

        if (event.key === "Escape") {
            event.preventDefault();
            cancelPreviewTimeout();
            props.onPreview?.(null);
            setQuery("");
            setIsOpen(false);
            setHoveredIndex(null);
            inputRef?.blur();
        }
    };

    const handleFocusOut = (event: FocusEvent) => {
        const nextTarget = event.relatedTarget;
        const currentTarget = event.currentTarget as HTMLDivElement | null;
        if (
            currentTarget &&
            nextTarget instanceof Node &&
            currentTarget.contains(nextTarget)
        ) {
            return;
        }
        cancelPreviewTimeout();
        props.onPreview?.(null);
        setHoveredIndex(null);
        setIsOpen(false);
    };

    return (
        <div
            class={styles.searchShell}
            onFocusIn={() => query().trim() && setIsOpen(true)}
            onFocusOut={handleFocusOut}
        >
            <input
                ref={inputRef}
                class={styles.searchInput}
                type="search"
                placeholder={
                    props.shortcutHint
                        ? `Search quantities (${props.shortcutHint})`
                        : "Search quantities"
                }
                value={query()}
                autocomplete="off"
                spellcheck={false}
                aria-label="Search quantities"
                aria-expanded={isOpen()}
                aria-controls="quantity-search-results"
                onInput={event => {
                    const nextQuery = event.currentTarget.value;
                    setQuery(nextQuery);
                    setIsOpen(nextQuery.trim().length > 0);
                }}
                onKeyDown={handleKeyDown}
            />
            <Show when={isOpen()}>
                <div class={styles.results} id="quantity-search-results" role="listbox">
                    <Show
                        when={results().length > 0}
                        fallback={<div class={styles.empty}>No matching quantities</div>}
                    >
                        <For each={results()}>
                            {(result, index) => (
                                <div
                                    class={styles.resultRow}
                                    onMouseEnter={() => {
                                        setHoveredIndex(index());
                                        schedulePreview(result.canonicalPath);
                                    }}
                                    onMouseLeave={() => {
                                        setHoveredIndex(null);
                                        schedulePreview(null);
                                    }}
                                >
                                    <button
                                        type="button"
                                        class={styles.result}
                                        classList={{
                                            [styles.active]: index() === activeResultIndex()
                                        }}
                                        role="option"
                                        aria-selected={index() === activeResultIndex()}
                                        onClick={() => commitSelection(result.canonicalPath)}
                                    >
                                        <span class={styles.resultName}>{result.name}</span>
                                        <span class={styles.resultPath}>{result.canonicalPath}</span>
                                    </button>
                                    <button
                                        type="button"
                                        class={styles.addButton}
                                        aria-label={`Add ${result.name} to selection`}
                                        title="Add to selection"
                                        onClick={() => addToSelection(result.canonicalPath)}
                                    >
                                        <svg viewBox="0 0 16 16" aria-hidden="true">
                                            <path
                                                d="M8 3v10M3 8h10"
                                                fill="none"
                                                stroke="currentColor"
                                                stroke-linecap="round"
                                                stroke-width="1.75"
                                            />
                                        </svg>
                                    </button>
                                </div>
                            )}
                        </For>
                    </Show>
                </div>
            </Show>
        </div>
    );
};

export default Search;