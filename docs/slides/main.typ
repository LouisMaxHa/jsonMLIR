#import "@preview/touying:0.7.4": *
#import themes.metropolis: *

#import "@preview/subpar:0.2.2"
#set par(justify: true)

#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node

#show raw: set text(font: "Hack Nerd Font Mono")

// https://forum.typst.app/t/how-to-use-a-different-cover-function-for-text-and-math-in-touying/5328/2
#let should-hide = state("cover-count", false)
#let hide-now-on() = context should-hide.update(true)
#let shade-now-on() = context should-hide.update(false)
#let cover-it(self:none, it) = context if should-hide.get() {hide(it)} else {utils.semi-transparent-cover(it, self:self, alpha:85%)}


#show: metropolis-theme.with(
  // config-methods(cover: cover-it),
  // config-methods(cover: utils.semi-transparent-cover.with(alpha: 70%)),
  config-info(
    title: [Chaîne de compilation pour Modane],
    subtitle: [Création de fonctions optimisées avec MLIR],
    author: [Louis-Max Harter],
    institution: [France],
    date: datetime.today(),
  ),
)



#title-slide()
#set align(horizon)
// #outline-slide(title: "Table des matières")

== Modane: Simplifier l'écriture de code
- Syntaxe haut niveau
- On décrit les opérations
#grid(
  columns: (1fr, 2fr),
  align(bottom)[
    #figure(
      ```m
      @ComputeLoop
        computeFjr
          in p,
          in C,
          in Ajr,
          in uj,
          in ur,
          out F {
        for (j in cells())
          for (r in nodesOfCell(j))
            F{j,r} = p{j} * C{j,r}
            + prodTensVec(Ajr{j,r}, (uj{j} - ur{r}));
      }
      ```,
      caption: [Modane],
    )
  ],
  pause,

  align(bottom)[
    #figure(
      ```m
      void computeFjr() {
        ENUMERATE_(Cell, j, defaultMesh()->allCells()) {
          NodeConnectedListView tmp_r_container = (*j).nodes();
          for(int r=0, nb_r=tmp_r_container.size(); r<nb_r; ++r) {
              m_F(j, r) = m_p[j] * m_C(j, r)
              + Arcane::math::prodTensVec(
                    m_Ajr(j, r),
                    (m_uj[j] - m_ur[tmp_r_container[r]]
                  )
              );
          }
        }
      }
      ```,
      caption: [Équivalent Arcane],
    )
  ],
)

/*
Cependant, lors de la génération de code C++, on perd en expréssivité,
Prenons pas example ces deux boucles
*/

== Niveau d'abstraction

#grid(
  columns: (1.5fr, 2fr),
  align(horizon + left)[
    - On travaille avec des boucles
    - On souhaite améliorer les performances
    - Quelles optimisations sont possibles ?
    - Est-ce que `-O3` suffira ?!
  ],
  [
    #pause
    #figure(
      ```cpp
      int main(){
        int somme = 0;
        int n = ??; /* Connu à l'éxécution seulement */

        /* somme de 0 à n-1 */
        for(int i = 0; i < n; i++){
          somme += i;
        }

        /* somme de n à 1 */
        for(int i = 0; i < n; i++){
          somme += n - i;
        }

        /* somme = n * n */
        std::cout << somme << st::endl;
      }
      ```,
      caption: [C++, deux boucles classiques],
    )
  ],
)

== LLVM vous avez dit ?

#figure(
  image("images/pipeline_llvm.png", width: 100%),
  caption: [LLVM pour la compilation],
)

/*
On peux espérer un résultat qui ressemble à deux boucles,
Mais en LLVM, que des jumps
*/
== LLVM IR généré

#columns(2, [
  #figure(
    image("images/loop_llvm_blocs.png", width: 80%),
    caption: [Résultat attendu],
  )
  #pause
  #figure(
    image("images/loop_llvm.png", width: 80%),
    caption: [Résultat obtenu],
  )
])

/*
Suite
*/
== MLIR à la rescousse

#grid(
  columns: (1fr, 1fr),
  [#uncover("2-")[
    *MLIR*: Multi-Level Intermediate Representation
    #v(0.5cm)
    - Plus haut niveau d'abstraction
    - Différents dialectes (LineAlg, Affine, GPU, ...)
    - Des optimisations de différents niveaux
      - loop-hoist-memref
      - stencil-unroll
      - stencil-inlining
      - ...
    - On descend ensuite en LLVM
  ]
  ],
  [
    #figure(
      image("images/loop_mlir.png", width: 100%),
      caption: [Résultat obtenu],
    )
  ],
)

== Petit récapitulatif
#figure(
  image("images/pipeline.png", width: 90%),  caption: [Organisation de la chaine de compilation (simplifiée)],
)

== Avec plus de détails !
#figure(
  image("images/pipeline_full.png", width: 90%),  caption: [Organisation de la chaine de compilation (honnête)],
)



== Description de fonction à générer
#grid(
  columns: (1.2fr, 1fr),
  [
    #figure(
      ```json
      { "op": "function",
        "name": "max",
        "args": [
          [ "x", "i64" ],
          [ "y", "i64" ]
        ],
        "body": [
          { "op": "if",
            "cond": {
              "op": "binary", "ope": ">",
              "lhs": { "name": "x" },
              "rhs": { "name": "y" }
            },
            "then": { "name": "x"},
            "else": { "name": "y"},
          }
        ]
      }
      ```,
      caption: [AST en Json],
    )
  ],
  pause,

  [
    #figure(
      image("images/python_ast.png", width: 100%),
      caption: [AST composé de structures python],
    )
  ],
)

== Génération du code MLIR
#grid(
  columns: (1fr, 2fr),
  [
    #figure(
      ```python
      class BinaryOp(OpNode):
        op: Literal["binary"]
            = "binary"
        lhs: BaseValue
        rhs: BaseValue
        ope: OperatorOp

        def codegen(
          self, builder: Builder
        ) -> Sequence[ValNode]:
          ...
      ```,
      caption: [Définition d'un noeud],
    )
  ],
  [
    #pause
    #figure(
      ```python
      def codegen(self, builder: Builder) -> Sequence[ValNode]:
          # Codegen recursif
          lhs = self.lhs.codegen(builder) # Noeud
          rhs = self.rhs.codegen(builder)

          # On récupère les valeurs SSA
          ssa_l = lhs.get_SSA()           # Valeur SSA
          ssa_r = rhs.get_SSA()

          # Génération de l'opération
          match self.ope.value:
              case "+":
                  op = AddiOp(ssa_l, ssa_r)
                  builder.insert(op)      # Opération jsonMLIR
                  ssa_result = op.result  # Valeur SSA

          # On renvoie le résultat
          return ValSSA(ssa_result)       # Noeud
      ```,
      caption: [Implémentation de `codegen()`],
    )
  ],
)

== Conclusion

- Votre compilateur ne peux pas faire plus que ce que vous lui donnez
- Nous avons besoin de plusieurs niveaux d'expressivité
- Pensez à ré-utiliser les briques existantes
- Faire son propre langage de programmation: c'est fun et atteignable !

#focus-slide[Merci pour votre attention ! \ Avez-vous des questions ?]
