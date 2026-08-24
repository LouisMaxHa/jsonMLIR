import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonList, jsonNumber, jsonObject, jsonString } from '../utils/json.js';
import { registerStruct, type FieldType } from '../variables/memory.js';
import { OpNode } from './codegen.js';

/** Discriminant is ``"define struct"`` (with a space), matching the Python schema. */
export class DefineStructOp extends OpNode {
    readonly op = 'define struct' as const;

    constructor(
        readonly name: string,
        readonly size: number,
        readonly fields: readonly FieldType[],
    ) {
        super();
        registerStruct(name, size, fields);
    }

    override codegen(): CGN {
        return jsonObject([
            ['op', jsonString(this.op)],
            ['name', jsonString(this.name)],
            ['size', jsonNumber(this.size)],
            ['fields', jsonList(this.fields.map(f => f.codegen()))],
        ]);
    }
}
