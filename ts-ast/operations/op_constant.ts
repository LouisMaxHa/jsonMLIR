import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { Scalar } from '../utils/enum_scalars.js';
import { jsonNumber, jsonObject, jsonString } from '../utils/json.js';
import { OpNode } from './codegen.js';

export class ConstOp extends OpNode {
    readonly op = 'const' as const;

    constructor(
        readonly val: number,
        readonly type: Scalar = Scalar.i64,
    ) {
        super();
    }

    override codegen(): CGN {
        // Always emit ``type`` so the JSON is self-describing; Python defaults to i64.
        return jsonObject([
            ['op', jsonString(this.op)],
            ['val', jsonNumber(this.val)],
            ['type', jsonString(this.type)],
        ]);
    }
}
