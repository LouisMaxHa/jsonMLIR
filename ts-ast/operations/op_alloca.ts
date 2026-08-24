import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonNumber, jsonObject, jsonString } from '../utils/json.js';
import type { TyNode } from '../variables/ty/ty_base.js';
import { OpNode } from './codegen.js';
import type { AllocSize } from './op_alloc.js';

export class AllocaOp extends OpNode {
    readonly op = 'alloca' as const;

    constructor(
        readonly name: string,
        readonly type: TyNode,
        readonly size: readonly AllocSize[] = [],
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['name', jsonString(this.name)],
            ['type', this.type.codegen()],
            [
                'size',
                this.size.length === 0
                    ? undefined
                    : jsonList(this.size.map(sizeCodegen)),
            ],
        ]);
    }
}

function sizeCodegen(size: AllocSize): CGN {
    if (typeof size === 'number') {
        return jsonNumber(size);
    }
    return size.codegen();
}
