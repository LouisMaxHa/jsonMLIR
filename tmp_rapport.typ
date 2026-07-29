
== Gestion et manipulation des variables <sec:variables>
=== Valeurs SSA

Contrairement au tutoriel de LLVM ou de MLIR qui utilise uniquement des flottants sur 64 bits, nous /*sujet*/ avons besoin de supporter plusieurs types de données (tableaux, scalaires, pointeurs...).
Ma /*sujet*/ première version consistait à simplement ignorer le type des valeurs manipulées. Cette première version bien que radicale /*adj*/ offre l'avantage de pouvoir supporter n'importe quel type sans avoir besoin d'implémenter une classe le décrivant. Une fois le code généré, MLIR se charge de vérifier que les types manipulés sont bien compatibles et nous /*sujet*/ renvoie une erreur dans le cas contraire.

Malheureusement, même cette version n'est pas si simple. LLVM, MLIR et xDSL ne permettent pas de créer des variables mutables, seulement des variables assignées une seule fois (SSA, Single Static Assignment).
Par example, dans le cas d'un branchement conditionnel pour renvoyer la plus grande valeur, LLVM va créer une variable pour chaque branche plutôt que de modifier une variable contenant la valeur maximum.
Le résultat sera ensuite récupéré en utilisant l'opérateur `phi` qui s'occupera de sélectionner la bonne variable selon le chemin emprunté à l'éxécution, la situation est résumée par la @fig:phi.

#figure(
  image("../images/phi.png", width: 40%),
  caption: [Opérateur phi - fusion SSA après branchement],
) <fig:phi>

L'utilisation de cette forme canonique permet de faciliter l'usage d'optimisations, par exemple :
- Constant folding - Simplifie les calculs avec les valeurs connues à la compilation (ex: constantes)
- Value range propagation - calcule les intervalles possibles des résultats, permettant d'anticiper les prédictions de branchement ou des #todo[ortho] les éliminer
- Dead-code elimination - suppression du code qui n'a aucun effet sur le résultat
- Global value numbering - remplacement des calculs dupliqués produisant le même résultat
- Register allocation - optimisation de l'utilisation des registres machine

Cependant, ces valeurs non mutables complexifient /*adj*/ le travail du développeur, qui doit ajouter des opérateurs phi et préciser quelle version de la variable utiliser en fonction du bloc précédent.
Pour simplifier l'utilisation de variables mutables, les développeurs de LLVM recommandent l'usage des opérateurs d'allocation@LLVM_ALLOCA. Par exemple, une variable `i` est allouée et son adresse n'est plus jamais modifée pour respecter la forme canonique SSA. La valeur de cette variable peut aussi être lu et sa valeur stockée dans une variable immutable qui servira dans d'autres opération. 

Cette méthode permet de contourner la restriction imposée par la forme canonique du SSA mais engendre donc un surcout important avec l'usage de getter/setter à chaque lecture et ecriture d'une variable.
Pour eviter de saturer l'usage de la mémoire avec des appels excessifs, il existe une passe d'optimisation nomée `mem2reg` dont le but est de convertir ces accès à la mémoire en des accès utilisant des registres. Le système de passes détaillé plus amplement dans la partie #todo(ref).

Ainsi, les valeurs flottantes `f64` deviennent des références vers des flottants `memref<f64>` qu'il faut différencier des tableaux de flottants `memref<10xf64>` (ici tableau de 10 éléments).
Ce changement rend impossible la comparaison directe entre le résultat d'une opération (`f64`) et une variable du même type (`memref<f64>`), il faut d'abord déréférencer la variable.
Par contre, la lecture d'un élément d'un tableau (`memref<?xf64>`) donnera directement un `f64` qu'il n'est pas nécessaire de déréférencer.

La différence entre le comportement des tableau et des valeurs scalaire implique un comportement différent selon le type de la valeur manipulée. Cette distinction sera d'autant plus nécéssaire que des types différents peuvent utiliser des dialectes différent, et donc, des accesseurs différents: pointeur utilisent `ptr.load` tandis qu'il faut utiliser `memref.load` pour les tableaux.

=== Variables typées

La seconde approche à introduit une classe par type de variable (scalaire, tableau, pointeur).
Une classe comprend alors une variable imutable contenant un descripteur `memref` qui pointe vers les données stockée.

Ces classes implémentent l'interface `Val` @fig:python-val-interface qui consiste en 4 méthodes:
- `load(indices)` : Permet de lire une valeur, les indices indiques la position de la valeur à lire
- `set(indices, valeur)` : Permet d'écrire une valeur, les indices indiques la position de la valeur à modifier
- `get_type()` : Renvoie la classe Python (Double, Array, Pointeur)
- `get_mlir_type()` : Renvoie le type MLIR (f64, descripteur memref, u64)


Une version simplifiée de ces structures en python disponible à la figure @fig:classes-val.
#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 1em,
    row-gutter: 1em,
    [
      #figure(
        ```python
        def Val:
          @abstractmethod
          def get_type() -> Val:
            pass

          @abstractmethod
          def get_mlir_type() -> Type:
            pass

          @abstractmethod
          def load(indices: List[str | Val]) -> SSAVariable:
            pass
        ```,
        caption: [Interface `Val`],
      ) <fig:python-val-interface>
    ],
    [
      #figure(
        ```python
        def Double(Val):
          addr # Memref<f64>

          def get_type() -> Val:
            Double(addr=None)

          def get_mlir_type() -> Type:
            F64Type.get()

          def load(indices) -> SSAVariable:
            return Memref.load(self.addr)

        ```,
        caption: [Classe `Double`],
      ) <fig:python-val-double>
    ],
    [
      #figure(
        ```python
        def Array(Val):
          addr      # Memref<??xVal>
          dimensions: List[int]
          base: Val # Type de la valeur contenu dans le tableau

          def get_type() -> Val:
            Array(addr=None, base=self.base)

          def get_mlir_type() -> Type:
            return MemRefType.get(self.dimension, self.base.get_mlir_type())

          def load(indices) -> SSAVariable:
            return Memref.load(self.addr, indices)
        ```,
        caption: [Classe `Array`],
      ) <fig:python-val-array>
    ],
    [
      #figure(
        ```python
        def Pointeur(Val):
          addr      # Memref<i64>
          base: Val # Type de la valeur pointée

          def get_type() -> Val:
            Pointeur(addr=None, base=self.base)

          def get_mlir_type() -> Type:
            IntegerType.get_signless(64)

          def load(indices) -> SSAVariable:
            addr = Memref.load(self.addr) 
            return Memref.load(addr)
        ```,
        caption: [Classe `Pointeur`],
      ) <fig:python-val-pointeur>
    ],
  ),
  caption: [Examples simplifié des classes utilisés],
) <fig:classes-val>

Dans le cas d'un tableau @fig:python-val-array, le nombre d'indices fournis doit correspondre à sa dimension..
Pour un pointeur @fig:python-val-pointeur, le premier indice doit être `*` pour indiquer que qu'il faut déréférencer la valeur pointée plutôt que de renvoyer l'adresse de la mémoire.
Pour une structure @fig:python-val-structure, le premier indice doit correspondre au nom d'un attribut de la structure.

Cette deuxième version permet d'avoir un comportement spécifique selon le type manipulé, mais cette implémentation possède deux défauts:
- Les types sont représenté par des instances avec des addresses nulles, ce qui n'est pas très pratique à manier
- Les opérations pour lire les valeurs renvoie les variables MLIR contenant le résultat, il n'est pas possible d'appeller `load` sur celles-ci. En l'état, il n'est pas possible de faire des pointeurs de pointeur.

=== Variables et instances séparées

==== Problème

La version précédente mélangeait deux rôles dans une même classe : décrire un type, et manipuler une valeur en mémoire.
Cela menait à deux limitations concrètes.

D'une part, un type était représenté par une instance « vide » (adresse nulle). On ne pouvait donc pas raisonner sur un type sans fabriquer un objet valeur artificielle, ce qui compliquait les comparaisons et les allocations.

D'autre part, `load` renvoyait directement une valeur SSA MLIR. Or une valeur SSA n'expose plus nos méthodes `load` / `store` : impossible, par exemple, de chaîner un accès sur un pointeur de pointeur, ou de continuer à indexer après avoir lu un élément de tableau.

==== Proposition

Nous /*sujet*/ séparons donc clairement trois responsabilités (@fig:classes-type-valeur) :

- `Ty` : description pure d'un type (scalaire, tableau, pointeur, structure...). Il ne contient aucune adresse.
- `Val` : instance concrète, composée d'un `Ty` et d'une référence mémoire. C'est elle qui implémente `load` et `store`.
- `Var` : simple nom de variable. Elle sert à retrouver la `Val` associée dans un registre global (le « heap » de variables), car toute valeur n'est pas forcément issue d'une variable nommée : certaines sont des résultats intermédiaires d'opérations.

#figure(
  image("../images/classes_type_valeur.png", width: 70%),
  caption: [Séparation des responsabilités entre `Ty`, `Val` et `Var`],
) <fig:classes-type-valeur>

Deux méthodes sur `Ty` suffisent pour dialoguer avec MLIR :
- `get_type()` : le type MLIR de la valeur elle-même (`f64`, `memref<10xf64>`, `i64` pour un pointeur...).
- `get_memref_type()` : le type utilisé pour _stocker_ cette valeur en mémoire (`memref<f64>` pour un scalaire, `memref<10xf64>` pour un tableau...).

Cette distinction reprend le constat de la @sec:variables : une variable mutable n'est jamais un `f64` nu, mais une case mémoire pointée par un descripteur `memref`.

Pour construire une `Val` à partir d'un type et d'une valeur SSA MLIR, nous /*sujet*/ utilisons une factory : elle choisit la bonne sous-classe (`ValScalar`, `ValMemref`, `ValPtr`...) selon le `Ty` fourni. Cela évite de disperser cette logique dans chaque opération du compilateur.

Une version simplifiée de cette hiérarchie est donnée aux @fig:classes-ty et @fig:classes-val-sep.

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 1em,
    row-gutter: 1em,
    [
      #figure(
        ```python
        class Ty:
          @abstractmethod
          def get_type(self) -> Type: ...
          @abstractmethod
          def get_memref_type(self) -> MemRefType: ...
        ```,
        caption: [Interface `Ty`],
      ) <fig:python-ty-interface>
    ],
    [
      #figure(
        ```python
        class TyScalar(Ty):
          def get_type(self):
            return F64Type.get()
          def get_memref_type(self):
            return MemRefType.get([], self.get_type())
        ```,
        caption: [Type scalaire],
      ) <fig:python-ty-scalar>
    ],
    [
      #figure(
        ```python
        class TyMemref(Ty):
          dimensions: list[int]
          base: Ty  # type des éléments

          def get_type(self):
            return MemRefType.get(
              self.dimensions,
              self.base.get_type(),
            )
          def get_memref_type(self):
            return self.get_type()
        ```,
        caption: [Type tableau],
      ) <fig:python-ty-memref>
    ],
    [
      #figure(
        ```python
        class TyPtr(Ty):
          base: Ty  # type pointé

          def get_type(self):
            # adresse ABI : entier 64 bits
            return IntegerType.get_signless(64)
          def get_memref_type(self):
            return MemRefType.get([], self.get_type())
        ```,
        caption: [Type pointeur],
      ) <fig:python-ty-ptr>
    ],
  ),
  caption: [Types (`Ty`) : description sans adresse mémoire],
) <fig:classes-ty>

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 1em,
    row-gutter: 1em,
    [
      #figure(
        ```python
        class Val:
          ty: Ty

          def get_ty(self) -> Ty:
            return self.ty

          @abstractmethod
          def load(self, indices) -> Val: ...
          @abstractmethod
          def store(self, indices, source: Val): ...
        ```,
        caption: [Interface `Val`],
      ) <fig:python-val-sep-interface>
    ],
    [
      #figure(
        ```python
        class ValScalar(Val):
          addr  # memref<f64>

          def load(self, indices) -> Val:
            # indices vides : lit le scalaire (valeur SSA)
            ssa = memref.LoadOp(self.addr, [])
            return ValSSA(ssa)
        ```,
        caption: [Valeur scalaire],
      ) <fig:python-val-sep-scalar>
    ],
    [
      #figure(
        ```python
        class ValMemref(Val):
          addr  # memref<?xT>

          def load(self, indices) -> Val:
            # consomme autant d'indices que de dimensions
            elem = memref.LoadOp(self.addr, indices)
            return Factory.from_SSA(self.ty.base, elem)
        ```,
        caption: [Valeur tableau],
      ) <fig:python-val-sep-memref>
    ],
    [
      #figure(
        ```python
        class ValPtr(Val):
          addr  # memref<i64>

          def load(self, indices) -> Val:
            # "*" : déréférencer, puis poursuivre
            ptr = memref.LoadOp(self.addr, [])
            val = Factory.from_SSA(self.ty.base, deref(ptr))
            return val.load(indices[1:])
        ```,
        caption: [Valeur pointeur],
      ) <fig:python-val-sep-ptr>
    ],
  ),
  caption: [Valeurs (`Val`) : type + adresse, accès via `load` / `store`],
) <fig:classes-val-sep>

Le point important est que `load` renvoie désormais une _nouvelle_ `Val`, et non plus une valeur SSA brute. On peut donc enchaîner les accès, quel que soit le type obtenu à chaque étape.

==== Accès récursifs

Les types composés (tableau de pointeurs, pointeur vers structure...) se traitent uniformément : chaque `Val` consomme la portion d'indices qui la concerne, puis délègue le reste à la valeur obtenue.

Concrètement, pour un tableau :
1. on découpe la liste d'indices en `consuming` (une entrée par dimension) et `remaining` (le reste) ;
2. s'il ne reste rien, on effectue directement le `store` (ou le `load`) ;
3. sinon, on charge l'élément à l'indice `consuming`, puis on rappelle `store` / `load` sur cet élément avec `remaining`.

Le même schéma s'applique aux structures (le premier indice est un nom de champ) et aux pointeurs (le premier indice est `*` pour déréférencer). Voici le principe pour un tableau :

```python
class ValMemref(Val):
    def store(self, index, source):
        consuming = index[: len(self.ty.dimensions)]
        remaining = index[len(self.ty.dimensions) :]

        if not remaining:
            memref.StoreOp(source.get_SSA(), self.addr, consuming)
            return

        # Charge l'élément, puis écrit plus loin
        self.load(consuming).store(remaining, source)
``` <lst:python-val-memref>

==== Exemple

Prenons un pointeur vers une matrice $5 times 5$ de structures `Noeud`, et l'affectation du champ `x` de l'élément $(1, 2)$ via :

`ptr.store(["*", 1, 2, "x"], 10.0)`

Chaque étape consomme une partie du chemin (@fig:boites-set) :
1. `ValPtr` voit `"*"` : il déréférence et obtient un `ValMemref` (la matrice) ;
2. `ValMemref` consomme `1, 2` : il charge l'élément et obtient un `ValStruct` ;
3. `ValStruct` consomme `"x"` : il localise le champ et y écrit `10.0`.

#figure(
  image("../images/boites.png", width: 100%),
  caption: [Appels récursifs de `load` / `store` pour `ptr.store(["*", 1, 2, "x"], 10.0)`],
) <fig:boites-set>

À chaque étape, la factory reconstruit la `Val` du type intermédiaire attendu. Si un accès aboutit à une valeur SSA « nue » (résultat d'une opération arithmétique, par exemple), elle est encapsulée dans une `ValSSA` : cela permet de la réutiliser en opérande, ou de la stocker ensuite dans un `memref` pour retrouver une valeur mutable.

Cette séparation `Ty` / `Val` / `Var` corrige les deux défauts de la version précédente : les types sont manipulables sans adresse fictive, et les accès composés (pointeurs de pointeurs, champs de structures dans des tableaux...) se chaînent naturellement.
