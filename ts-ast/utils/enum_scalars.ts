/**
 * Scalar kinds accepted by jsonMLIR (mirrors ``jsonmlir.utils.enum_scalars.Scalar``).
 * MLIR-specific helpers (``get_type`` / ``from_type``) are intentionally omitted.
 */

export enum ScalarFamily {
    int = 'int',
    float = 'float',
    idx = 'index',
}

export enum Scalar {
    i64 = 'i64',
    i32 = 'i32',
    i16 = 'i16',
    i8 = 'i8',
    i1 = 'i1',
    I64 = 'I64',
    I32 = 'I32',
    I16 = 'I16',
    I8 = 'I8',
    I1 = 'I1',
    f16 = 'f16',
    f32 = 'f32',
    f64 = 'f64',
    f80 = 'f80',
    f128 = 'f128',
    idx = 'index',
}

const BYTE_SIZES: Record<Scalar, number> = {
    [Scalar.i1]: 1,
    [Scalar.I1]: 1,
    [Scalar.i8]: 1,
    [Scalar.I8]: 1,
    [Scalar.i16]: 2,
    [Scalar.I16]: 2,
    [Scalar.f16]: 2,
    [Scalar.i32]: 4,
    [Scalar.I32]: 4,
    [Scalar.f32]: 4,
    [Scalar.i64]: 8,
    [Scalar.I64]: 8,
    [Scalar.f64]: 8,
    [Scalar.idx]: 8,
    [Scalar.f80]: 10,
    [Scalar.f128]: 16,
};

const INT_SCALARS = new Set<Scalar>([
    Scalar.i64, Scalar.i32, Scalar.i16, Scalar.i8, Scalar.i1,
    Scalar.I64, Scalar.I32, Scalar.I16, Scalar.I8, Scalar.I1,
]);

const FLOAT_SCALARS = new Set<Scalar>([
    Scalar.f16, Scalar.f32, Scalar.f64, Scalar.f80, Scalar.f128,
]);

export function byteSize(scalar: Scalar): number {
    return BYTE_SIZES[scalar];
}

export function kindOf(scalar: Scalar): ScalarFamily {
    if (INT_SCALARS.has(scalar)) {
        return ScalarFamily.int;
    }
    if (FLOAT_SCALARS.has(scalar)) {
        return ScalarFamily.float;
    }
    return ScalarFamily.idx;
}

export function parseScalar(value: string | Scalar): Scalar {
    if (typeof value !== 'string') {
        return value;
    }
    const found = (Object.values(Scalar) as string[]).find(s => s === value);
    if (found === undefined) {
        throw new Error(`Unknown scalar type: ${value}`);
    }
    return found as Scalar;
}
