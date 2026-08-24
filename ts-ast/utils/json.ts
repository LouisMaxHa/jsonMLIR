import {
    CompositeGeneratorNode as CGN,
    expandToNode,
    joinToNode,
} from 'langium/generate';

/** JSON string literal, e.g. `"foo"`. */
export function jsonString(value: string): CGN {
    return expandToNode`${JSON.stringify(value)}`;
}

/** JSON number (or `null` for a dynamic dimension). */
export function jsonNumber(value: number | null): CGN {
    return expandToNode`${value === null ? 'null' : String(value)}`;
}

export type JsonEntry = readonly [string, CGN | undefined];

/**
 * Object whose entries with an `undefined` value are omitted
 * (avoids trailing / orphan commas for optional fields).
 */
export function jsonObject(entries: readonly JsonEntry[]): CGN {
    const present = entries.filter((e): e is readonly [string, CGN] => e[1] !== undefined);
    return expandToNode`{
        ${joinToNode(
            present,
            ([key, value]) => expandToNode`${jsonString(key)}: ${value}`,
            { separator: ',', appendNewLineIfNotEmpty: true },
        )}
    }`;
}

/** Compact one-line JSON array. */
export function jsonArray(items: readonly (CGN | undefined)[]): CGN {
    const present = items.filter((x): x is CGN => x !== undefined);
    return expandToNode`[${joinToNode(present, { separator: ', ' })}]`;
}

/** Multi-line JSON array (pretty-printed body). */
export function jsonList(items: readonly (CGN | undefined)[]): CGN {
    const present = items.filter((x): x is CGN => x !== undefined);
    return expandToNode`[
        ${joinToNode(present, { separator: ',', appendNewLineIfNotEmpty: true })}
    ]`;
}
