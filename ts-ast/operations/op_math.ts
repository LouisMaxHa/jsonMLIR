import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';
import type { MathOperator } from './op_operator.js';

export class MathOp extends OpNode {
    readonly op = 'math' as const;

    constructor(
        readonly ope: MathOperator,
        readonly value: BaseValue,
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['ope', jsonString(this.ope)],
            ['value', this.value.codegen()],
        ]);
    }
}
