import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../../utils/json.js';
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
}
