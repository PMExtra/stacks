# Stack maintenance rules

Apply these defaults when adding or maintaining any stack:

- Use `${TAG:-latest}` for the image tag so operators can override it.
- Configure environment variables only when required for deployment or when
  intentionally changing application defaults; do not repeat defaults unnecessarily.
- Do not leave commented-out code or configuration placeholders. Use environment
  variables for simple optional settings; do not add a separate enablement switch.
  Publish optional Compose structure in `optional/compose.*.yaml` and enable it
  with a stack-local symlink. Keep explanatory comments where useful.
- Choose `environment` entries or `env_file: .env` case by case. Favor explicit
  entries for a small set of variables operators usually configure, and `env_file`
  for many optional advanced settings usually left at application defaults.
  These are tendencies, not hard rules. Passing additional non-sensitive stack
  variables such as `TAG` through `env_file` is acceptable. Compose's
  `.env` interpolation does not itself pass values into the container;
  `environment` entries override `env_file` values. Keep required-value validation.
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
