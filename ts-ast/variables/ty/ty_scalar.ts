import { CompositeGeneratorNode as CGN, expandToNode } from 'langium/generate';

import { Scalar } from '../../utils/enum_scalars.js';
import { jsonString } from '../../utils/json.js';
import { TyNode } from './ty_base.js';

export class TyScalar extends TyNode {
    constructor(readonly scalar: Scalar) {
        super();
    }

    override codegen(): CGN {
        return expandToNode`${jsonString(this.scalar)}`;
    }
}
