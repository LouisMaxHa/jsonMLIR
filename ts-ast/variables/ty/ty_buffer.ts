import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonArray, jsonNumber, jsonObject, jsonString } from '../../utils/json.js';
import { TyNode } from './ty_base.js';
import { TyStruct } from './ty_struct.js';

/**
 * Byte buffer over a struct layout. JSON form is
 * ``{ "buffer": [dim…, "structName"] }`` where the base is the
 * **struct name string**, not a nested type object.
 */
export class TyBuffer extends TyNode {
    constructor(
        readonly dimensions: readonly (number | null)[],
        readonly base: TyStruct,
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['buffer', jsonArray([
                ...this.dimensions.map(d => jsonNumber(d)),
                jsonString(this.base.name),
            ])],
        ]);
    }
}
