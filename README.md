# Python Graphwalker

## Intro

Python-Graphwalker is a tool for testing based on finite state
machine graphs. Graphwalker reads FSMs specified by graphs, plans
paths, calls model methods by name from graph labels and reports
progress and results.

While conceptually derived from the Graphwalker project,
(implemented in java) this is a complete reimplementation from that
initial concept.

Notably, there are a few differences:

-   In the original, nodes are considered states to be verified and
    edges actions to be taken, but this version has no ambition to
    enforce this convention in any way, even though it is quite
    useful.

-   Python Graphwalker does not understand extended FSM labels. It
    should ignore them, but proceed at your own risk until this is
    definitively dealt with one way or the other.

-   Python Graphwalker is quite promiscuous about letting you load
    and combine code to implement the different components of the
    design. Some combinations don't make sense.


![The graph for the self-test of the Interactive planner.
](graphwalker/test/examples/selftest.png)



## Overall design

The idea that has driven the design is that the graph-problems are
quite orthogonal to the testing actions and that the problem of
reporting the results are orthogonal to both. The graph-problems
are further decomposable into path planning, stop conditions and of
course loading graph files.

The added feature request to be able save and replay the path of a
run dissolve into the path-recorder reporting class and the plain
text graph loader.

The design is separated into these parts:

-   Model, (normally) supplied by the user as a graph file.

-   Stop condition, which bool-converts to true if its conditions
    are met.

-   Planner, which uses the model and stop condition to provide an
    iterable of plan steps as (id, name, ...) tuples.

-   Reporter, which is called on execution events.

-   Taps, installed by the reporter system to capture side-effects.
    (currently stdout/stderr and logging)

-   Actor supplied by the user as an object with function
    attributes, normally an object instance.

-   Executor that, for each step in the plan, calls the reporter
    and looks up and calls the named method on the actor. In addition
    to the step methods, it also calls a few other methods, if present
    on the actor.


### Code loader

There is a common code-loader interface, so it's easy to load
custom code and supply arguments (if any, if callable) from the
command line:

-   --foo=module.module

-   --foo=module.module.function

-   --foo=module.module.class:argument,...,keyword=value,...


If the object found is callable, it will be called, with any
arguments supplied, and the result used.

## Formats

Currently, Python Graphwalker understands a few simple file
formats:

### graphml

Graphs for the original Graphwalker are typically drawn using
[yEd], which normally produces graphml files, so support for these
have been a priority.

[_yEd]: http://www.yworks.com/en/products\_yed\_about.html

### dot/graphviz

Plain graphviz files can also be written, which turns out to be
useful: The Cartographer reporter uses dot to generate highlighted
maps as it goes.

### plain text

Plain text word lists are interpreted as a linear list of nodes to
visit. Comments of the familiar "/\* ... \*/" form are respected,
as are line comments of both the "\#" and "//" varieties. If the
first node isn't labeled "Start", such a node is added.

### other formats

Other formats are easy enough to add. All that you need to supply
for a reader is an iterable of vertex (id, label) pairs and an
iterable of (id, label, from-id, to-id) quadruples. Graphwalker
will convert these to its internal formats. For write-support, you
need to take a similar pair of sequences, but with the difference
that for the vertex and edge tuples might be longer.

## Planners

The steps to be executed by the executor are determined by one or
more planners. Normally, planners are expected to examine the
supplied graph and plan a traversal of it, but the lack of
enforcement creates a few special opportunities.

Planners are instantiated through the common code-loader interface,
so it's easy to plug in your own planner. They're called with a
graph and a StopCond instance to supply an iterable containing
tuples of at least two elements, as the executor expects id and
label.

To generate repeatable plans, use the seed keyword argument as
planners keep their own random number generators.

### Random

The simplest planner, Random, traverses the graph by randomly
choosing an edge and visiting that edge and the target vertex until
the StopCond is satisfied. It does not check the StopCond between
edge and vertex.

#### Example
`graphwalker --stopcond=Coverage --planner=Random:seed=1337 model.dot`

### Goto

To visit specific vertices, name them as arguments to the Goto
planner. In addition to names and ids, 'random' will pick a vertex
at random. If there is more than one candidate, the one closest to
the current vertex will be chosen. (So this does not, currently,
minimize the total path.)

An integer for the keyword argument 'repeat' will repeat the name
list. (but not, nota bene, the specific vertices.) A repeat of zero
will be taken to mean infinity.

#### Example
`graphwalker --planner=Goto:happy,random,sad,repeat=10 model.dot`

### Euler

To visit all edges in the graph most efficiently, we'd like to
generate an [Eulerian trail]. Since the graph is not necessarily
even (semi-)Eulerian, the Euler planner copies the graph and
modifies it. First, by cutting out the forced steps from the Start
vertex source subgraph. The graph is then 'eulerized' by adding
edges to make it Eulerian. (in-degree equal to out-degree for all
vertices) After the plan is created it run through the StopCond, to
get rid of extraneous steps at the end.

[Eulerian trail]: http://en.wikipedia.org/wiki/Eulerian\_trail

#### Example
`graphwalker --planner=Euler model.dot`

### Interactive

There's often a wish to choose paths as the test is running when
developing or debugging models. When run, Interactive lists the
edges of the current vertex and prompts for input. You can choose a
listed edge by entering it's number, or you can use one of the
special commands:

| command  | effect
| -------- | -------------------------------------------
| g, goto  | Goes to the specified vertex*
| f, force | Send some arbitrary name(s) as plan steps
| j, jump  | Set some new vertex* as the current one
| d, debug | Enter the pdb debugger
| q, quit  | End the plan

*: asks if there's more than one by the name given

#### Notes about entering the debugger
If you quit from the debugger,
you quit from the whole program. Catching BdbQuit exceptions
doesn't seem to work, instead, use c/continue

You can set breakpoints in, for instance, other planners, that will
drop you back into the debugger after you've left it.

## StopConds - When to stop

Some planners have inherent stopping conditions, others don't, so
there are independent conditions that can be applied to the plans.
It's up to the planner to consult them, to they don't always cut
the test off optimally, or at all.

### Coverage

The default stop condition is coverage of 100% of edges, which
means that it will signal completion when it's seen all the edges
in the graph. It can also require some percentage of vertices, or
some percentage of each. The percentages are given as keywords
arguments named 'edges' and 'verts' or 'vertices'.

##### Examples
`graphwalker --stopcond=Coverage:edges=100,verts=50 model.dot`

`graphwalker --stopcond=Coverage:vertices=25 model.dot`

### SeenSteps

Ignoring the difference between edges and vertices, SeenSteps will
simply be done when it has seen all the steps it's looking for. The
steps are given as an argument list.

##### Examples
`graphwalker --stopcond=SeenSteps:a,e_once,b model.dot`

### CountSteps

Again ignoring the difference between edges and vertices, simply
counts the test steps and signals when some number of steps have
been taken. The number of steps is the first argument, or the
keyword argument 'steps', defaulting to 100.

##### Examples
`graphwalker --stopcond=CountSteps:52 model.dot`

`graphwalker --stopcond=CountSteps:steps=52 model.dot`

## Actor

The test executor simply uses getattr to look up callables by the
names supplied by the planner, so you can implement the test code
as a module, a class, or, using the programmatic interface,
basically any object you like.

The callables on the test object are called without arguments for
now.

In addition to the labels in the graph, a few administrative
methods are also called, if present:

-   *setup* is called at the start of the test session with a
    dictionary containing the other instances involved in the test: the
    reporter, the model, and so on. Notably, if you want to save
    attachments from the test methods, you should use the reporter
    instance here.

-   *step\_begin* is called before each step with the step
    definition. The step definition is an iterable where the first is
    the id and the second the name of the step.

-   *step\_end* is called before after each step like step\_begin,
    but with the addition of a failure, usually None. If the test
    failed, or there was some other exception, step\_end is called with
    that exception, typically an AssertionError. The step\_end method
    can permit the testing to continue by returning the exact string
    "RECOVER".

-   *teardown* is called the same way as setup, at the end.


## Reporters

To report the results of the tests, the reporters are all called
for each event, notably step\_begin and step\_end.

### Print

Simply print to stdout (default) or stderr, controlled with the
keyword argument output. If you are using the programming
interface, you can send any file-like, writable object. Note that
combinations of Log and Print quickly get really confusing.

##### Examples
`graphwalker --reporter=Print:output=stderr model.dot`

### Log

Emits to the standard python logger. The name of the logger
defaults to the name of the reporting module, but can be set via
the keyword argument 'logger'. The level can also be set with the
keyword argument 'level'. Note that combinations of Log and Print
quickly get really confusing.

##### Examples
`graphwalker --reporter=Log:logger=moo,level=WARN model.dot`

### PathRecorder

The PathRecorder simply saves the plan step names to a text file,
so that the run can be replicated by feeding recording to the
plain-text graph reader. The directory where the file is saved
defaults to '.' but can be given as the keyword argument 'path'.
Likewise name defaults to the test name but can be set with the
keyword argument 'name'. The 'attach' keyword argument, if set (at
all) makes it try to attach it.

##### Examples
`graphwalker --reporter=PathRecorder:path=/tmp,name=steps model.dot`

`graphwalker --reporter=PathRecorder:attach=true,name=steps model.dot`

### Cartographer

To map the progress of the test graphically, the Cartographer
reporter emits graphviz files with the current step highlighted.
The keyword arguments 'dotpath' and 'imgpath' control where the
graphviz input and output files go, respectively, bot defaulting to
'.'. The image type defaults to PNG but can be set using the
keyword argument 'imgtype'. The 'attach' keyword argument, if set
(at all) makes it try to attach it.

##### Examples
`graphwalker --reporter=Cartographer model.dot`

`graphwalker --reporter=Cartographer:imgtype=jpg,attach=1 model.dot`

`graphwalker --reporter=Cartographer:dotpath=/tmp,imgpath=./www model.dot`

## Taps

Currently, the there are only taps for streams and the logging
system. Both the logging tap and taps of standard out & error are
included by default.

## Future

Graphwalker itself needs a lot more, and a lot more devious tests.

## Authors

The first iteration of the Python port of Graphwalker was written
by Viktor Holmberg, Harald Hartwig and Chongyang Sun under the
direction of Nils Österling (tester) and Anders Eurenius
(developer).

This iteration was rewritten from scratch by Anders Eurenius to
incorporate everything we learned from the first.

## License

The license we have chosen is the Apache License, version 2.0. You
should find the full text in the file named "LICENSE.txt".

