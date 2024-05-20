set positional-arguments


default:
  @just --list

test testname="run":
  hatch run test:{{testname}}

release:
  # Push to main to ensure that any outstanding changes are uploaded first
  git push origin main
  # Tag the branch
  git tag v$(hatch version)
  # Push the new tag and fire off the release
  git push --tags