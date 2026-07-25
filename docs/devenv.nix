{ config, ... }:

{
  languages = {
    javascript = {
      enable = true;
      npm.enable = true;
      npm.install.enable = true;

      directory = "./docs";
    };
  };

  processes.docs = {
    cwd = "${config.git.root}/docs";
    exec = "npm run dev";
  };
}
