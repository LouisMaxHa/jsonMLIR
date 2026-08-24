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
