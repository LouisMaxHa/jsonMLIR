import { CompositeGeneratorNode as CGN } from 'langium/generate';

import { jsonArray, jsonNumber, jsonObject } from '../../utils/json.js';
import { TyNode } from './ty_base.js';

export class TyMemref extends TyNode {
    constructor(
        readonly dimensions: readonly (number | null)[],
        readonly base: TyNode,
    ) {
        super();
    }

    override codegen(): CGN {
        return jsonObject([
            ['memref', jsonArray([
                ...this.dimensions.map(d => jsonNumber(d)),
                this.base.codegen(),
            ])],
        ]);
    }
}
