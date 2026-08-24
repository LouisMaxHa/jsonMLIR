/**
 * Binary / comparison / logical operators (mirrors ``OperatorOp``).
 * Values are the JSON tokens emitted in the ``"ope"`` field.
 */
export enum Operator {
    plus = '+',
    minus = '-',
    times = '*',
    divide = '/',
    divideF = '/f',
    plusF = '+f',
    minusF = '-f',
    timesF = '*f',
    and = 'and',
    or = 'or',
    xor = 'xor',
    equals = '==',
    notEquals = '!=',
    gt = '>',
    lt = '<',
    ge = '>=',
    le = '<=',
}

export enum UnaryOperator {
    neg = '-',
    not = '!',
}

export enum MathOperator {
    sqrt = 'sqrt',
}

export function parseOperator(ope: string | Operator): Operator {
    if (typeof ope !== 'string') {
        return ope;
    }
    const found = (Object.values(Operator) as string[]).find(v => v === ope);
    if (found === undefined) {
        throw new Error(`Unknown binary operator: ${ope}`);
    }
    return found as Operator;
}

export function parseUnaryOperator(ope: string | UnaryOperator): UnaryOperator {
    if (typeof ope !== 'string') {
        return ope;
    }
    const found = (Object.values(UnaryOperator) as string[]).find(v => v === ope);
    if (found === undefined) {
        throw new Error(`Unknown unary operator: ${ope}`);
    }
    return found as UnaryOperator;
}

export function parseMathOperator(ope: string | MathOperator): MathOperator {
    if (typeof ope !== 'string') {
        return ope;
    }
    const found = (Object.values(MathOperator) as string[]).find(v => v === ope);
    if (found === undefined) {
        throw new Error(`Unknown math operator: ${ope}`);
    }
    return found as MathOperator;
}
