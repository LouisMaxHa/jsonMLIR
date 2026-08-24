import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../utils/json.js';
import { OpNode } from './codegen.js';
import type { BinaryOp } from './op_binary.js';
import type { CallOp } from './op_call.js';
import type { ConstOp } from './op_constant.js';
import type { UnaryOp } from './op_unary.js';
import type { VarOp } from './op_var.js';

export type SetValue = BinaryOp | ConstOp | VarOp | CallOp | UnaryOp;

export class SetOp extends OpNode {
    readonly op = 'set' as const;

    constructor(
        readonly var_: VarOp,
        readonly val: SetValue,
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['var', this.var_.codegen()],
            ['val', this.val.codegen()],
        ]);
    }
}
