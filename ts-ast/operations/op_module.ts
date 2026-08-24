import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonObject, jsonString } from '../utils/json.js';
import type { ModuleStatement } from './base.js';
import { OpNode } from './codegen.js';

export class ModuleJsonOp extends OpNode {
    readonly op = 'module' as const;

    constructor(readonly body: readonly ModuleStatement[] = []) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['body', jsonList(this.body.map(s => s.codegen()))],
        ]);
    }
}
