import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonArray, jsonNumber, jsonString } from '../utils/json.js';
import { TyNode } from './ty/ty_base.js';

/** Field descriptor for ``define struct``: ``[name, type, offset, size]``. */
export class FieldType {
    constructor(
        readonly name: string,
        readonly type: TyNode,
        readonly offset: number,
        readonly size: number,
    ) {}

    codegen(): CGN {
        return jsonArray([
            jsonString(this.name),
            this.type.codegen(),
            jsonNumber(this.offset),
            jsonNumber(this.size),
        ]);
    }
}

/** Registered struct layout (populated by ``DefineStruct`` / ``DefineStructOp``). */
export type StructDef = {
    name: string;
    /** Declared layout size (may include padding). */
    size: number;
    fields: readonly FieldType[];
};

/** Global registry of struct definitions, keyed by name. */
export const structsRegistry = new Map<string, StructDef>();

export function registerStruct(
    name: string,
    size: number,
    fields: readonly FieldType[],
): void {
    structsRegistry.set(name, { name, size, fields });
}

export function lookupStruct(name: string): StructDef {
    const def = structsRegistry.get(name);
    if (def === undefined) {
        throw new Error(
            `Struct ${JSON.stringify(name)} is not defined. `
            + 'Call DefineStruct before querying its size.',
        );
    }
    return def;
}
