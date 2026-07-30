{ pkgs, ... }:

{
  packages = [
    pkgs.git
  ];

  languages = {
    python = {
      enable = true;
      package = pkgs.python311;
      uv = {
        enable = true;
        sync.enable = true;
      };
      venv.enable = true;
    };
  };

  git-hooks.hooks = {
    fumero-generate = {
      enable = true;
      name = "fumero generate";
      entry = "uv run fumero generate fumero";
      files = "^src/fumero/.*\\.py$";
      pass_filenames = false;
    };

    fumero-init = {
      enable = true;
      name = "fumero init";
      entry = "uv run fumero init docs/src/components/mdx/pdx.tsx";
      files = "^src/fumero/assets/.*\\.tsx$";
      pass_filenames = false;
    };

    ruff.enable = true;
    ruff-format.enable = true;

    ty = {
      enable = true;
      name = "ty";
      entry = "uv run ty check";
      files = "\\.py$";
      pass_filenames = false;
    };
  };
}
