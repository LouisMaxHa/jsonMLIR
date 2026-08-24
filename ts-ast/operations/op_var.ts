import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonNumber, jsonObject, jsonString } from '../utils/json.js';
import type { TyNode } from '../variables/ty/ty_base.js';
import { OpNode } from './codegen.js';

/** An index into a variable: integer, field name / ``"*"``, or nested ``VarOp``. */
export type VarIndex = number | string | VarOp;

export class VarOp extends OpNode {
    readonly op = 'var' as const;

    constructor(
        readonly name: string,
        readonly indices: readonly VarIndex[] = [],
        readonly type?: TyNode,
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['name', jsonString(this.name)],
            [
                'indices',
                this.indices.length === 0
                    ? undefined
                    : jsonList(this.indices.map(indexCodegen)),
            ],
            ['type', this.type?.codegen()],
        ]);
    }
}

function indexCodegen(index: VarIndex): CGN {
    if (typeof index === 'number') {
        return jsonNumber(index);
    }
    if (typeof index === 'string') {
        return jsonString(index);
    }
    return index.codegen();
}
