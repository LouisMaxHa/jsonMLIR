/**
 * Reconstruction of ``examples/somme/main.json`` via the TypeScript DSL.
 *
 * Run (from a project that has ``langium`` installed and can resolve this
 * folder) with something like:
 *
 *   npx tsx example.ts
 *
 * and compare the printed JSON to ``examples/somme/main.json``.
 */
import {
    Binary,
    Const,
    Function,
    generateJson,
    Module,
    Set,
    Var,
    While,
} from './index.js';

const module = Module([
    Function(
        'lib_main',
        [['max', 'i64']],
        [
            Set(Var('toto', [], 'i64'), Const(0)),
            Set(Var('i', [], 'i64'), Const(0)),
            While(
                Binary('<', Var('i'), Var('max')),
                [
                    Set(
                        Var('toto'),
                        Binary('+', Var('toto'), Var('i')),
                    ),
                    Set(
                        Var('i'),
                        Binary('+', Var('i'), Const(1)),
                    ),
                ],
            ),
            Var('toto'),
        ],
    ),
]);

console.log(generateJson(module));
