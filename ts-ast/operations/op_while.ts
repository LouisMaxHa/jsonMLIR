import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';

export class WhileOp extends OpNode {
    readonly op = 'while' as const;

    constructor(
        readonly cond: BaseValue,
        readonly thenBlock: readonly BaseValue[] = [],
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['cond', this.cond.codegen()],
            ['thenBlock', jsonList(this.thenBlock.map(s => s.codegen()))],
        ]);
    }
}
