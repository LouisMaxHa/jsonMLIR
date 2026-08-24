import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject } from '../../utils/json.js';
import { TyNode } from './ty_base.js';

/** Pointer / address: ABI size is always 8 bytes (i64). */
const PTR_BYTE_SIZE = 8;

export class TyPtr extends TyNode {
    constructor(readonly base: TyNode) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['addr', this.base.codegen()],
        ]);
    }

    override byteSize(): number {
        return PTR_BYTE_SIZE;
    }
}
