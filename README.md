# Chaos Monkey

Chaos Monkey provides tooling for injecting errors, instrumenting degraded conditions or causing outages, in a Juju environment. It's used within Juju's continuous integration and testing process to harden Juju core features, as well as charms and bundled solutions, against adverse conditions. 

Chaos Monkey is installed from the [Charm Store](https://jujucharms.com/u/juju-qa/chaos-monkey) by simply running `juju deploy cs:~juju-qa/trusty/chaos-monkey`. Once deployed it can be related to any service; Juju actions can then be used to release chaos on a service unit. See The [Charm Store Readme](https://jujucharms.com/u/juju-qa/chaos-monkey) for more detail.

The Chaos Monkey charm pulls it's library of chaos operations and the runner application from this repository. The charm installs the code on each service unit with which it has a relationship and when the start action is called, the runner is executed.

Using the Chaos Monkey charm is the recommended way to use the library. However, if you would like to add chaos routines see the following instruction.

## Adding Chaos

Chaos operations are written in Python. Examples of existing operations can be seen under the [chaos/](https://github.com/juju/chaos-monkey/blob/master/chaos) directory. Operations are grouped by type, for example chaos related to the network can be found in [chaos/net.py](https://github.com/juju/chaos-monkey/blob/master/chaos/net.py) and chaos related to killing processes or rebooting a service unit can be found in [chaos/kill.py](https://github.com/juju/chaos-monkey/blob/master/chaos/kill.py). 

In the code, a python class is the mechanism used to define a chaos type. This class needs to be derived from the `ChaosMonkeyBase` class, found in [chaos_monkey_base.py](https://github.com/juju/chaos-monkey/blob/master/chaos_monkey_base.py). `ChaosMonkeyBase` enforces that the child class implement the get_chaos method, which must return a list of Chaos object instances. The `Chaos` base class can also be found in [chaos_monkey_base.py](https://github.com/juju/chaos-monkey/blob/master/chaos_monkey_base.py). Each operation for a given type is implemented as a pair of class methods; one method for enabling and one for disabling the chaos. References to these enable and disable methods are returned to the runner application when it calls get_chaos().
Lastly, if a new class has been added, its factory() meathod needs to be added to the factory list in `ChaosMonkey.get_all_chaos()` in [chaos_monkey.py](https://github.com/juju/chaos-monkey/blob/master/chaos_monkey.py), which will allow the operations provided by the new class to be discovered when the runner is invoked.

## Invoking the runner

Chaos can be run as standalone on the local system by executing `python runner.py` (use --help to see the usage and full list of options). Use caution, since the chaos operations will affect your local system. When testing it's advisable to run in a virtual machine or container. A better solution is to use the [Chaos Monkey charms chaos-source configuration option](https://jujucharms.com/u/juju-qa/chaos-monkey#charm-config-chaos-source) to set a URL to the source you'd like to run and let the charm hooks upgrade to the new source.
