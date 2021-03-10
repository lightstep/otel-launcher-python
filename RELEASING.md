# Releasing

Once all the changes for a release have been merged to main, ensure the following:

- [ ] version has been updated in `src/opentelemetry/launcher/version.py`
- [ ] tests are passing
- [ ] user facing documentation has been updated

# Publishing

Publishing to [pypi](https://pypi.org/project/opentelemetry-launcher/) is automated via GitHub actions. Once a tag is pushed to the repo, a new GitHub Release is created and package is published  via the actions defined here: https://github.com/lightstep/otel-launcher-python/blob/main/.github/workflows/release.yml

The commit that gets tagged must be in `main`, so do this _after_ merging a release PR.

```
$ git clone git@github.com:lightstep/otel-launcher-python && cd otel-launcher-python
# ensure the version matches the version beind released
$ cat src/opentelemetry/launcher/version.py
__version__ = "0.0.1"
$ git tag v0.0.1 && git push origin v0.0.1
```
