import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../../utils/json.js';
import { lookupStruct } from '../memory.js';
import { TyNode } from './ty_base.js';

export class TyStruct extends TyNode {
    readonly name: string;

    constructor(base: string) {
        super();
        this.name = base;
    }

    override codegen(): CGN {
        return jsonObject([
            ['struct', jsonString(this.name)],
        ]);
    }

    /**
     * Sum of each field's declared ``size`` (padding between fields is not
     * included — use the ``size`` passed to ``DefineStruct`` for the full layout).
     */
    override byteSize(): number {
        const def = lookupStruct(this.name);
        return def.fields.reduce((acc, field) => acc + field.size, 0);
    }
}
