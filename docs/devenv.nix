{ pkgs, config, ... }:

{
  languages = {
    javascript = {
      enable = true;
      npm.enable = true;
      npm.install.enable = true;

      directory = "./docs";
      package = pkgs.nodejs_22;
    };
  };

  processes.docs = {
    cwd = "${config.git.root}/docs";
    exec = "npm run dev";
  };
}
