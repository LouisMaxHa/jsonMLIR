import { CompositeGeneratorNode as CGN, toString } from 'langium/generate';

/** Base class for every jsonMLIR AST operation that can emit JSON. */
export abstract class OpNode {
    abstract readonly op: string;
    abstract codegen(): CGN;

    toJson(): string {
        return toString(this.codegen());
    }
}
