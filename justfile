set positional-arguments


default:
  @just --list

test testname="run":
  hatch run test:{{testname}}
