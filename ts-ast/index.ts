import { toString } from 'langium/generate';

import type { ModuleJsonOp } from './operations/op_module.js';

export * from './operations/index.js';
export * from './utils/enum_scalars.js';
export * from './variables/ty/index.js';
export {
    FieldType,
    lookupStruct,
    registerStruct,
    structsRegistry,
    type StructDef,
} from './variables/memory.js';

/** Render a module AST to the JSON string consumed by jsonMLIR. */
export function generateJson(module: ModuleJsonOp): string {
    return toString(module.codegen());
}
