import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject } from '../../utils/json.js';
import { TyNode } from './ty_base.js';

export class TyPtr extends TyNode {
    constructor(readonly base: TyNode) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['addr', this.base.codegen()],
        ]);
    }
}
