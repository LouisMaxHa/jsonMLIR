import { parseScalar, type Scalar } from '../../utils/enum_scalars.js';
import { TyNode } from './ty_base.js';
import { TyBuffer } from './ty_buffer.js';
import { TyMemref } from './ty_memref.js';
import { TyPtr } from './ty_ptr.js';
import { TyScalar } from './ty_scalar.js';
import { TySOA } from './ty_SOA.js';
import { TyStruct } from './ty_struct.js';

export { TyNode } from './ty_base.js';

/**
 * Build a ``TyNode`` from a JSON description or an existing node.
 *
 * Accepted forms:
 * - scalar : ``"i64"`` / ``"index"`` / …
 * - struct : ``{ struct: "name" }``
 * - memref : ``{ memref: [dim…, base] }``
 * - soa    : ``{ soa: [dim…, structName] }``
 * - buffer : ``{ buffer: [dim…, structName] }``
 * - addr   : ``{ addr: base }``
 */
export function parseTy(value: unknown): TyNode {
    if (value instanceof TyNode) {
        return value;
    }

    if (typeof value === 'string') {
        return new TyScalar(parseScalar(value));
    }

    if (value !== null && typeof value === 'object') {
        const obj = value as Record<string, unknown>;

        if ('addr' in obj) {
            return new TyPtr(parseTy(obj['addr']));
        }

        if ('memref' in obj) {
            const items = obj['memref'] as unknown[];
            const base = parseTy(items[items.length - 1]);
            const dimensions = items.slice(0, -1).map(d =>
                d === null || d === undefined ? null : Number(d),
            );
            return new TyMemref(dimensions, base);
        }

        if ('soa' in obj) {
            const items = obj['soa'] as unknown[];
            const baseName = items[items.length - 1];
            if (typeof baseName !== 'string') {
                throw new Error(`SOA base must be a struct name string, got ${JSON.stringify(baseName)}`);
            }
            const nElements = items.slice(0, -1).map(d =>
                d === null || d === undefined ? null : Number(d),
            );
            return new TySOA(new TyStruct(baseName), nElements);
        }

        if ('buffer' in obj) {
            const items = obj['buffer'] as unknown[];
            const baseName = items[items.length - 1];
            if (typeof baseName !== 'string') {
                throw new Error(`Buffer base must be a struct name string, got ${JSON.stringify(baseName)}`);
            }
            const dimensions = items.slice(0, -1).map(d =>
                d === null || d === undefined ? null : Number(d),
            );
            return new TyBuffer(dimensions, new TyStruct(baseName));
        }

        if ('struct' in obj) {
            return new TyStruct(String(obj['struct']));
        }

        if ('name' in obj) {
            return new TyStruct(String(obj['name']));
        }
    }

    throw new Error(`Unrecognized type description: ${JSON.stringify(value)}`);
}

export function parseTyOrScalar(value: string | TyNode | Scalar): TyNode {
    if (value instanceof TyNode) {
        return value;
    }
    if (typeof value === 'string') {
        return parseTy(value);
    }
    return new TyScalar(value);
}
