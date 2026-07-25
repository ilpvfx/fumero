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
}
