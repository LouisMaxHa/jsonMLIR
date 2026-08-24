import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonArray, jsonList, jsonObject, jsonString } from '../utils/json.js';
import type { TyNode } from '../variables/ty/ty_base.js';
import type { BaseValue } from './base.js';
import { OpNode } from './codegen.js';

export type FunctionArg = readonly [string, TyNode];

export class FunctionOp extends OpNode {
    readonly op = 'function' as const;

    constructor(
        readonly name: string,
        readonly args: readonly FunctionArg[] = [],
        readonly body: readonly BaseValue[] = [],
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['name', jsonString(this.name)],
            ['args', jsonList(this.args.map(([n, t]) =>
                jsonArray([jsonString(n), t.codegen()]),
            ))],
            ['body', jsonList(this.body.map(s => s.codegen()))],
        ]);
    }
}
