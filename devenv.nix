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
    ruff.enable = true;

    ty = {
      enable = true;
      name = "ty";
      entry = "uv run ty check";
      files = "\\.py$";
      pass_filenames = false;
    };
  };
}
