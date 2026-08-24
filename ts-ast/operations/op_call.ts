import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonObject, jsonString } from '../utils/json.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';

export class CallOp extends OpNode {
    readonly op = 'call' as const;

    constructor(
        readonly name: string,
        readonly args: readonly BaseValue[] = [],
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['name', jsonString(this.name)],
            ['args', jsonList(this.args.map(a => a.codegen()))],
        ]);
    }
}
