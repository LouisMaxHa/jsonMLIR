import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonArray, jsonNumber, jsonObject, jsonString } from '../../utils/json.js';
import { TyNode } from './ty_base.js';
import { TyStruct } from './ty_struct.js';

/**
 * Structure-of-arrays. JSON form is ``{ "soa": [n…, "structName"] }``
 * where the base is the **struct name string**, not a nested type object.
 */
export class TySOA extends TyNode {
    constructor(
        readonly base: TyStruct,
        readonly nElements: readonly (number | null)[],
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['soa', jsonArray([
                ...this.nElements.map(d => jsonNumber(d)),
                jsonString(this.base.name),
            ])],
        ]);
    }
}
