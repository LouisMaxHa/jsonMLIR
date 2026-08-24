import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';

/** Discriminant is ``"if"`` (not ``"cond"``), matching the Python schema. */
export class CondOp extends OpNode {
    readonly op = 'if' as const;

    constructor(
        readonly cond: BaseValue,
        readonly thenBlock: readonly BaseValue[],
        readonly elseBlock?: readonly BaseValue[],
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['cond', this.cond.codegen()],
            ['thenBlock', jsonList(this.thenBlock.map(s => s.codegen()))],
            [
                'elseBlock',
                this.elseBlock === undefined
                    ? undefined
                    : jsonList(this.elseBlock.map(s => s.codegen())),
            ],
        ]);
    }
}
