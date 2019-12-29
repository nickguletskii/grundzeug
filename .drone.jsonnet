local PipelineTesting(python_version) = {
  kind: "pipeline",
  name: "testing",
  platform: {
    os: "linux",
    arch: "amd64",
  },
  steps: [
    {
      name: "test",
      image: "python:" + python_version,
      pull: "always",
      commands: [
        "pip3 install --no-cache-dir --upgrade -r dev-requirements.txt",
        "pytest --cov=grundzeug tests"
      ],
    },
  ],
  trigger: {
    branch: [ "master" ],
    event: [ "pull_request" ],
  },
};

[
  PipelineTesting("3.7"),
  PipelineTesting("3.8"),
]