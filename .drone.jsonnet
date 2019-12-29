local PipelineTesting(python_version, trigger) = {
  kind: "pipeline",
  name: trigger + "/testing-python-" + python_version,
  type: "docker",
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
  trigger:
    if trigger == "pull_request"
    then {
        event: [ "pull_request" ],
    } else {
        branch: [ "master" ],
    },
};

[
  PipelineTesting(python_version, trigger)
  for python_version in ["3.7", "3.8"]
  for trigger in ["master", "pull_request"]
]