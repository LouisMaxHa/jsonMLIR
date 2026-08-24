import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';
import type { Operator } from './op_operator.js';

export class BinaryOp extends OpNode {
    readonly op = 'binary' as const;

    constructor(
        readonly ope: Operator,
        readonly lhs: BaseValue,
        readonly rhs: BaseValue,
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['ope', jsonString(this.ope)],
            ['lhs', this.lhs.codegen()],
            ['rhs', this.rhs.codegen()],
        ]);
    }
}
