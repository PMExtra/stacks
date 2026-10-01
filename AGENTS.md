# Stack maintenance rules

Apply these defaults when adding or maintaining any stack:

- Use `${TAG:-latest}` for the image tag so operators can override it.
- Configure environment variables only when required for deployment or when
  intentionally changing application defaults. Keep optional settings commented
  with a short explanation; do not repeat defaults unnecessarily.
- Omit `platform` by default so Docker selects the host architecture from the
  image manifest. Check supported architectures rather than assuming third-party
  images are multi-platform.
- For images maintained by this project, include and validate at least
  `linux/amd64` and `linux/arm64` in the build and release process.
- Keep necessary security settings and operational behavior. Document specific
  compatibility or security reasons for exceptions to these defaults. For example,
  databases may require an explicit version to avoid automatic major upgrades.

These rules guide new work; do not bulk rewrite existing stacks or change their
runtime behavior merely to conform. Keep changes scoped to the requested stack.
Operate stacks through `./upgrade`; validate Compose configuration without pulling
images or starting services unless the task explicitly requires it.
