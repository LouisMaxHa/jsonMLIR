import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';

export class PrintOp extends OpNode {
    readonly op = 'print' as const;

    constructor(readonly value: BaseValue) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['value', this.value.codegen()],
        ]);
    }
}
