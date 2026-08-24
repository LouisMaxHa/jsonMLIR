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

    override byteSize(): number {
        let n = 1;
        for (const d of this.dimensions) {
            if (d === null) {
                throw new Error(
                    `Cannot compute byteSize of memref with dynamic dimension: ${JSON.stringify(this.dimensions)}`,
                );
            }
            n *= d;
        }
        return n * this.base.byteSize();
    }
}
