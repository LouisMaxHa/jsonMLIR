import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';
import type { UnaryOperator } from './op_operator.js';

export class UnaryOp extends OpNode {
    readonly op = 'unary' as const;

    constructor(
        readonly ope: UnaryOperator,
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
