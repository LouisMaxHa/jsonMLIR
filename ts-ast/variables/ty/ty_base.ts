import { CompositeGeneratorNode as CGN } from 'langium/generate';

/**
 * Abstract type node. ``codegen()`` emits the JSON form expected by
 * ``jsonmlir.variables.ty.ty.parse_ty``.
 */
export abstract class TyNode {
    abstract codegen(): CGN;
}
