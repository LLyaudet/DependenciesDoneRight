# DependenciesDoneRight

by Laurent Frédéric Bernard François Lyaudet

A POC in Python to show that dependencies can be done right
with multiple installed versions of the same package.

## All started with a rant in a commit

See commit: https://github.com/LLyaudet/DevOrSysAdminScripts/commit/d4aa104a0f1cd78f4fbb5ee74814a04c0f176266

```
Why one venv for each Python dependency ?
Because no language of my knowledge did it right to handle all
possible dependency conflicts.
So in case of such a conflict, one specialized venv can get you out
of any problem.
The best solution would have been to allow install of different
versions of the same package, and have a mechanism:
- first intent, use the latest available version of a package among
those that satisfy the declared dependency constraints of the package
that has this dependency;
- second intent, check a dependency overload configuration file
with tree structure: if calling python package is A version 1.1.1
with dependency B itself with dependency C, use B 2.2.2 and C 3.3.3;
you could have along that another rule saying that when called
directly B 2.2.2 should use C 4.4.4;
and even more complicated:
if calling python package is A version 1.1.1 with dependency B and D
both themselves with dependency C, use B 2.2.2, D 0.1.0,
and C 3.3.3 for B, and C 4.4.4 for D;
once you've seen that it can never be more complicated than that,
once the same version number guarantees that the code is the same,
you create a config language "à la CSS" for cascading dependencies ;)
XD fit into JSON the dumbest possible way and you stop bothering
about dependency conflicts for the rest of history of informatics.
{
 "A":{
  "1.1.1": {
    "B": {
      "2.2.2": {
        "C": {
           // Dumb, you did not found it by yourself? Failed exam.
          "3.3.3" : {}
        }
      }
    },
    "D": {
      "0.1.0": {
        "C": {
           // Dumb, you did not found it by yourself? Failed exam.
          "4.4.4" : {}
        }
      }
    }
  },
  "B": {
    "2.2.2": {
      "C": {
        // Dumb, you did not found it by yourself? Failed exam.
        "4.4.4" : {}
      }
    }
  }
}
Wonderful someone rediscovered nested structures XD
Seriously so many engineers or computer scientists are dumb to cry.
```

This rant was based on an idea I had many years ago.

## Scope of the present POC

I did not implement all the features in my rant.
But I already implemented the biggest step needed in terms of
features: To be able to have a correct dependency version based
on the current version of the importing code
(previous step of the chain of imports, instead of all the chain).

With that, you can already solve many dependency conflicts,
when you have a dependency lagging behind, you can "freeze" its
dependencies, and have your other dependencies move forward.

## Pros and cons, known limitations

Biggest pro: Totally opt-in, you can mix packages with a single
default version, with packages that have multiple installed versions.
From this, there is almost no performance penalty if you don't use it.
**It brings new solutions without taking anything away from you.**
If the POC was implemented in C code of CPython,
the performance penalty would be negligible.

Not "spec full feature" yet, but most interesting feature is here.

Not solving the software stack below,
if you have incompatible compiled binaries using shared objects
in your Python packages, then it will not solve this.
I call this "shitty pants":
You have to clean the guy and the pants XD;
now the pants can be cleaned (almost, just a POC);
for C or other languages and shared objects, the guy will need more
cleaning ;).
(It could be done also,
but that's a distinct and multi-life long project ;) XD.)
Note that "shitty pants" is frequent and not an excuse for not solving
what can be solved at one level. ("Make it work" as your boss says.)

Not "Python full feature" yet.
Relative imports like ".a" do not work,
since it would require to modify "import" on top of "__import__".
(Could be solved by a version modifying CPython.)
Some parts of the standard library like importlib are not overriden
in this POC like reload that uses sys.modules for example.
(Could be solved with more work.)

To make it easy for users, it needs concerted effort on the package
managers software and the Python interpreter.
Note that a PEP could be written that specifies the way both may
interact
(this POC gives only proposals, but some details could be improved).
Then the Python interpreters could implement the feature,
and only then the needed developments could be done in pip or other
software, since the feature is backward compatible.

Biggest con: Fight the bureaucracy of many software projects to make
it happen. Welcome Inertia ;P XD.

Very nasty bugs may be possible with this approach.

There may be pros and cons in terms of security: Allowing upgrades
with smaller steps may be a gain if you check everything
(source code audit) before upgrading.
But the dynamic nature of all the imports after that may be quite a
burden to handle in terms of security and possible exploits.
Moreover, it may favorize that some unsecured versions are kept in the
code base for a longer time;
usually, the fact that all your code base uses a single version of a
package complicates the upgrade, but once upgraded you're safer
since known vulnerabilities have been corrected.

## How it works?

Keeping the structure of a venv,
the goal is to have some packages installed in a "versioned" way.
Such an install is materialized by the use of:
```
  site-packages/my_package/1.1.1/
                          /2.2.2/
                          etc.
```
instead of:
```
  site-packages/my_package/
```
The .dist-info files are already versioned,
nothing to change for them,
just allow that there can be multiple ones for the same package.
Example:
```
├── python_dependencies_done_right_A
│   ├── 1.1.1
│   │   └── __init__.py
│   ├── 2.2.2
│   │   └── __init__.py
│   └── 3.3.3
│       └── __init__.py
├── python_dependencies_done_right_B
│   ├── 1.1.1
│   │   └── __init__.py
│   ├── 2.2.2
│   │   └── __init__.py
│   └── 3.3.3
│       └── __init__.py
├── python_dependencies_done_right_C
│   ├── 1.1.1
│   │   └── __init__.py
│   ├── 2.2.2
│   │   └── __init__.py
│   └── 3.3.3
│       └── __init__.py
├── python_dependencies_done_right_D
│   ├── 1.1.1
│   │   └── __init__.py
│   ├── 2.2.2
│   │   └── __init__.py
│   └── 3.3.3
│       └── __init__.py
```
This is the responsibility of the package manager, like pip, to fill
the following two files on install and updates:
```
  versioned_packages.json,
  default_dependencies_versions.json.
```
The provisional location of these files is in site-packages/,
for example.
Another file `custom_dependencies_versions.json` must be at the same
location.

Filling versioned packages is trivial,
it can be an option like:
```
  pip install --versioned_package my_package=1.1.1 .
```
In such a case, pip would have to add my_package in the list
`versioned_packages.json` if not present,
and convert any "unversioned" previous single install of my_package
into a versioned one (mkdir and mv -r),
then install correctly as a versioned install the new version of
my_package (mkdir -p with one more intermediate directory).
Note that a versioned package can have unversioned dependencies,
and the other way around is possible.
It is a manual decision of the user to "version" any dependency with a
targeted reinstall.
An option `--versioned_package_and_dependencies` would not be hard
to implement,
in order to "version" all dependencies outside of builtins.
Example of `versioned_packages.json`:
```
{
  "d_d_r_versioned_A": "2.2.2",
  "d_d_r_versioned_B": "2.2.2",
  "d_d_r_versioned_C": "2.2.2",
  "d_d_r_versioned_D": "3.3.3"
}
```
This is a JSON dict, that gives at the same time the default (latest)
installed version.

(Technical detail, I used A, B, C, D for level of imports,
but later below I consider `versioned_A` and `unversioned_A` that are
distinct packages.
Maybe it will help you to think that
`versioned_A`, `versioned_B`, `versioned_C`, `versioned_C`
are `versioned_E`, `versioned_F`, `versioned_G`, `versioned_H`.)

Filling `default_dependencies_versions.json` is also quite trivial,
you just need to compare the cardinal product of installed
packages versions by itself,
with the dependencies constraints of all such packages in a loop.
If a constraint says
"Package A needs package B between 1.1.1 and 4.4.4" for example:
if B is not "versioned",
then you just check that the unique version is correct,
otherwise you need to find a version of B that is OK for all packages
as usual (output an error if no such version exists);
if B is versioned,
you fill `default_dependencies_versions.json` with a line with 
A (or A x.x.x if A is multi-version) needs latest installed compatible
version of B that is y.y.y,
if such a compatible version does not exist,
you install the latest compatible one
(in a versioned way along the existing one(s),
B is already versioned).
You can loop on the installs in the order you want,
you can not have an infinite loop
since there is a finite number of versions to install,
the trivial "Rinse & repeat/recursive calls" approach just works.
Example of default_dependencies_versions.json:
```
{
  "d_d_r_unversioned_A": {
    "d_d_r_versioned_B": "1.1.1",
    "d_d_r_versioned_C": "2.2.2"
  },
  "d_d_r_versioned_A/1.1.1": {
    "d_d_r_versioned_B": "1.1.1",
    "d_d_r_versioned_C": "1.1.1"
  },
  "d_d_r_versioned_A/2.2.2": {
    "d_d_r_versioned_B": "2.2.2",
    "d_d_r_versioned_C": "2.2.2"
  },
  "d_d_r_unversioned_B": {
    "d_d_r_versioned_D": "1.1.1"
  },
  "d_d_r_versioned_B/1.1.1": {
    "d_d_r_versioned_D": "2.2.2"
  },
    "d_d_r_versioned_B/2.2.2": {
    "d_d_r_versioned_D": "3.3.3"
  },
  "d_d_r_unversioned_C": {
    "d_d_r_versioned_D": "3.3.3"
  },
  "d_d_r_versioned_C/1.1.1": {
    "d_d_r_versioned_D": "2.2.2"
  },
    "d_d_r_versioned_C/2.2.2": {
    "d_d_r_versioned_D": "1.1.1"
  }
}
```

The cherry on the cake is just a by-product:
you can fill a file:
```
custom_dependencies_versions.json
```
that overloads `default_dependencies_versions.json`.
Example of `custom_dependencies_versions.json`:
```
{}
```
no overloading, or
```
{
  "d_d_r_unversioned_A": {
    "d_d_r_versioned_B": "2.2.2"
  },
  "d_d_r_versioned_A/1.1.1": {
    "d_d_r_versioned_C": "2.2.2"
  }
}
```

### Structure of the examples of the POC

4 levels of import: A B C D

Each module or submodule defines `wat()` printing the package and
its version.

A imports B C D<br>
B is imported normally, with its submodule B.b<br>
C is imported from the submodule A.a de A<br>

B imports D<br>
D is imported with its submodule D.d<br>

C imports D
D is imported with its submodule D.d

hence on A level:
  from B import D as BD
  from B import d as Bd
  from C import D as CD
  from C import d as Cd

  A.wat()
  a.wat()
  B.wat()
  b.wat()
  C.wat()
  c.wat()
  BD.wat()
  Bd.wat()
  CD.wat()
  Cd.wat()

Everything is doubled with U and V prefixes,
for unversioned et versioned.

Look at venv_skeleton in this repository to see the Python code of the
dependencies.

## Help needed

If you have a taste for cleaning stuff, writing a nice PEP,
and fight bureaucracy, then go ahead ! :)

I do not expect to have the time of doing this for a predictable
future.
I licensed this code with MIT license, so that there is no reason
you may be reluctant to improve.
Moreover, a PR on CPython for the feature would only keep the big
lines, but be new code.

The PEP should address where are located the JSON files.
If some of these files could be splitted in files for each path
in PATH.
Note that since it is possible to have dependencies in different paths
of PATH, only the first JSON file would be easy to have on many
locations.
Handling a cascade of "customs" would be easy also.
But the "default dependencies relations" would be hard to fill
across many paths.

## Further discussion

To extend on that,
this solution works for solvable dependency conflicts.
I exchanged with people in Python discourse there:
https://discuss.python.org/t/dependencies-conflicts/105582/9
To explain my arguments there (sorry for the harsh tone):
- a remark was done about the case of incompatible data structures
between 2 versions of the same dependency library;
my technical answer was:
```
To give a full answer to your remark on data structures:
Your code is your responsibility.
When you use library A and library B and their data structures are not
compatible,
you do more or less boilerplate code to modify data structures so that
they communicate through your code.
Now, it is exactly the same problem,
if you have to make data structures of A 1.1.1 communicate with
A 2.2.2.
You just do the same kind of boilerplate code.
It may be inefficient, but it works.
In Python, it may be just looping on the elements of the “in”
structure to make it a new “out” structure.
Once everything is dealed with on the levels below,
you do the required “interfacing” work
(not to be confused with the restricted meaning of an interface
in OOP).
```
before that my two rant answers were:
```
Classical “Nay-saying” and Not at all pertinent.
In my suggestion, the default mechanism is unchanged.
What I suggest is an overloading mechanism.
I do agree that with such mechanisms you can always shot yourself in
the foot.
But at least you have full control and all the dependency conflicts
can be resolved if you assume that any released version had a working
dependency set.
My solution removes the blocking points of the current solution.
If you do no matter what, and use a set of dependencies that has no
way to work, then it doesn’t work; but it’s “tautological”.
The only real drawback of giving this full power to the user is that
it may be used by crackers to do no matter what once they have set
foot on the PC of someone else.
But usually they do no matter what with or without this option.
It’s just another thing to know about your system.
```
```
Sorry for the harsh tone, but @some_guy@ moved my topic from Ideas to
Python Help which is inappropriate and looks kind of
censorship/downgrading behind good looking noob management.
```

After that, I answered to multiple objections that are not really
technical:
```
  "citation": not going to fly
It is ambiguous when you say that it is not going to fly.
It may mean “You can always ask, but nobody will do the change.”
which is probable, whilst the fact that it would not work is false.

For the users having to structure their code,
it is only if they need to handle such interfacing problems.
So nothing is taken away from users, they don’t loose anything.
They just have new solutions: for all dependencies conflicts below,
they have a simple solution,
for dependencies conflicts in their own code,
they have a way to handle it through boilerplate code.
It brings solutions to the table,
previously they had none other than looking for other packages
as dependencies or recode part of a dependency.
Nothing is perfect, nothing is free of some burden,
nothing justifies that on Internet the majority of persons that react
are nay-sayers.
  "citation": no performance penalty argument
A solution with a performance penalty *notable only when it is used*
is always better than no solution.
Your argument is a classical fake argument of nay-sayers
and doesn’t imply that they always do very optimized code.
Moreover, when the Python interpreter resolves an import it must load
the function tokens and their adresses to use them afterward;
resolving two imports for two distinct versions of the same library
would prepare similarly what is needed to use some adress when some
function token is parsed without conflicting because of the distinct
contexts (or the distinct tokens in the user code),
I see no reason that the interpreter would be slowed down apart of the
additional tokens to keep in memory;
the penalty for the performance and memory would be measured;
it would be mainly on the import mechanism that it could be slowed
down very slightly in my opinion,
and once the import is done,
I see no reason for a substantial penalty.
If you think otherwise, please explain your reasoning.

 " citation": it works only for toy projects, years of experience,
    try it
Fine, when you say that, you perfectly know that the entry cost on a
project like Python is high, and that almost nobody has the time
to understand the internals of a project like Python just to make a
proof of concept and experience further bashing afterwards.
I’m already struggling to redo most of my own Free Software work
because of sabotage.
Weeks or months of work that vanishes in thin air.
I’m always struggling because of crackers and intelligence services
and I don’t know who mess with my code to enshittify my life.
If I take now two weeks of work to make a proof of concept,
I am almost certain that they will not let me succeed or find a way
to screw another of my projects during the time.
I don’t have yet taken the decision to do or not a proof of concept
but you don’t imagine how mad I am against people that steal the life
of others and nobody helps.
```

Then the person I just answered to,
kindly suggested that it can be done in pure Python,
without needing to know the internals of Python in C,
but just modifying import.
But he was still thinking that there would be serious drawbacks
that I don't see.
Note that it is only partly true, the current POC is in pure Python,
but knowing the internals of Python in C would be required for
"Python full feature" as noted previously.

Another people also answered:
  "citation": spec easy, craft difficult
and I responded:
```
Do you care to explain where are the identified blocking points?
From my point of view, you need the following ingredients:
 - given current state of the interpreter it is currently executing
   the code of the following import (package and version)
   thus any new import there is resolved by consulting the overloading
   file for dependencies if any, and backing on the default mechanism
   (it can move inside the tree of nested dependencies in the
   overloading in parallel of the moves inside the code,
   when it is outside of this tree, it only needs to check when it’s
   back at the root in case further code executed is in an existing
   branch)
   when an import is processed the current context gets the right
   adresses for tokens,
   tokens are resolved with the right adresses in the current context
   as usual.
I don’t see a conceptual blocking point.
If there is an ingredient of an interpreter that is relevant
and that I don’t see, please point at it.
```
This analysis was crude, and I did things differently.
I did the simple and most useful case where I load a versioned module,
check in `versioned_packages.json`
 => no performance penalty for anyone not using my feature!
And I can know when an import occurs there,
that the current module has "this name, this version".
(Fed up of having to battling with fake argument
"Cannot be done efficiently".).
Put it with a versioned name in sys.modules
(it should never conflict and the only possible drawback may be that
there will be more modules in sys.modules);
(note that since B is versioned or not, you can never need
to have to add "B" and "B:x.x.x" in sys.modules,
checking if the import is done in A or in A' will always yield a
search in sys.modules with "B:x.x.x" or "B:x'.x'.x'".),
alias for context and execute.
To be efficient, my code has to do:
- only one JSON import for versioned_packages.json,
  same for default_dependencies_versions.json,
  and custom_dependencies_versions.json, so it needs to go in a global
  init/pre-execute of the Python "launcher";
  problem with interactive mode (TODO),
  needs a command to reload these files,
  no responsibility if the user does funny things like using pip in
  one shell in parallel of using python3 in interactive mode
  in another shell,
  it must already be bugged in such case,
- import demanded,
- get current module name and version
  (maybe top version of main program is a problem
  since it is outside pypi, I need to think about it,
  since the dependency file is used to fill the venv or the docker),
- if current name and version in versioned_packages.json
  (I can cheat the previous point here,
  with a fake entry in versioned_packages.json
    "MyDjangoProject": { "1.1.1": ... },
  matched with a constant of the current code like
    MAIN_ID_FOR_DEPENDENCY_VERSIONNING="MyDjangoProject"
  in my Python main code
  using a default version 1.1.1, not a true problem, positive people
  will probably have better ideas for that, need to have that constant
  in all files context),
- check `custom_dependencies_versions.json` for a match between
  "A and B", save for later the matching B version if match
- if no match, check `default_dependencies_versions.json` for a match
  between "A and B",
  guaranteed to work for versioned packages, no bug,
  save for later the matching B version if match
- lookup sys.modules using the B version if found
- use standard import if no version needed,
- if version needed, custom import,
- make sure to fill sys.modules with the versioned name in such case.
My answer on Discourse before the above analysis had the following
drawbacks :
- Ok the spec guarantees that you do not jump between branches of
  dependencies, and that you only go upward or downward in the tree
  of `custom_dependencies_versions.json`.
  But "doubling" the work of executing the Python code and following
  where we are in `custom_dependencies_versions.json` would be slower.
  The POC limits to simple A -> B and B -> C independently
  avoids that.
  Otherwise I need a stack:
    on module change stack the element*s* needed,
    if I got A -> B -> C and code in A does import B.C as C,
    I need to keep track that when I call C.wat() I add "B:x.x.x"
    and "C:y.y.y" AND "Return-2" to the stack.
    If I do an import in C.wat(), I must use the stack to know if
    some ""suffix after ignoring "Return-i" values"" of it matches
    a branch rooted at the top
    in custom or `default _dependencies_versions.json`.
    The same stack must be used at the initial import execution of
    code in C.
Proof that the dynamic "cursor" in `custom_dependencies_versions.json`
is unique: I want the longest matching branch,
    if I'm outside of the starting branch (too deep),
    the suffix (top) of the stack may match another
    smaller branch beginning.
    Customizing fully is not a requirement, and the default only uses
    branches of depth 1, but the longest branch is unique,
    and the "roots" tags are also unique,
    so only one cursor at a time.

