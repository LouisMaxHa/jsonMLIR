import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonArray, jsonList, jsonObject, jsonString } from '../utils/json.js';
import type { TyNode } from '../variables/ty/ty_base.js';
import { OpNode } from './codegen.js';
import type { FunctionArg } from './op_function.js';

export class DefineFunctionOp extends OpNode {
    readonly op = 'define_function' as const;

    constructor(
        readonly name: string,
        readonly args: readonly FunctionArg[] = [],
        readonly returnTypes: readonly TyNode[] = [],
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
            ['return_types', jsonList(this.returnTypes.map(t => t.codegen()))],
        ]);
    }
}
